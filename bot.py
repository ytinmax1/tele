import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from config import BOT_TOKEN, YOUR_USER_ID, CHANNELS

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != YOUR_USER_ID:
        return
    await update.message.reply_text(
        "🤖 البوت شغال!\n\n"
        "ابعت أي رسالة وهخيرك تنشرها في أي قناة، وبعدين هسألك للتأكيد.\n"
        "يدعم: نصوص، صور، فيديوهات، ملفات، استيكرات، استطلاعات رأي، وكل حاجة تانية.\n\n"
        "/channels - عشان تشوف القنوات المتصلة"
    )

async def channels_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != YOUR_USER_ID:
        return
    if not CHANNELS:
        await update.message.reply_text("❌ مفيش أي قنوات متصلة بالبوت حالياً.")
        return
        
    text = "📢 القنوات المتصلة:\n\n"
    for i, ch in enumerate(CHANNELS, 1):
        text += f"{i}. `{ch}`\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != YOUR_USER_ID:
        await update.message.reply_text("❌ مش مصرح لك.")
        return

    if not CHANNELS:
        await update.message.reply_text("❌ مفيش قنوات متصلة عشان أنشر فيها. ضيف قنوات في ملف الإعدادات الأول.")
        return

    # Store the message details
    context.user_data['msg_id'] = update.message.message_id
    context.user_data['chat_id'] = update.effective_chat.id

    # Create keyboard for channel selection
    keyboard = []
    for i, ch in enumerate(CHANNELS, 1):
        keyboard.append([InlineKeyboardButton(f"قناة {i} ({ch})", callback_data=f"select_channel_{ch}")])
    
    # Option for all channels if there's more than one
    if len(CHANNELS) > 1:
        keyboard.append([InlineKeyboardButton("📢 كل القنوات", callback_data="select_channel_all")])
        
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "اختر القناة اللي عايز تنشر فيها الرسالة دي:",
        reply_markup=reply_markup,
        reply_to_message_id=update.message.message_id
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != YOUR_USER_ID:
        await query.answer("❌ مش مصرح لك.", show_alert=True)
        return

    await query.answer()
    data = query.data

    if data == "cancel":
        await query.edit_message_text("تم الإلغاء ❌")
        context.user_data.clear()
        return

    if data.startswith("select_channel_"):
        channel = data.split("_")[2]
        context.user_data['selected_channel'] = channel
        
        # Ask for confirmation
        channel_name = "كل القنوات" if channel == "all" else f"القناة ({channel})"
        keyboard = [
            [InlineKeyboardButton("✅ نعم، انشر الآن", callback_data="confirm_post")],
            [InlineKeyboardButton("❌ لا، إلغاء", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"⚠️ تأكيد النشر:\nهل أنت متأكد أنك تريد النشر في {channel_name}؟",
            reply_markup=reply_markup
        )
        return

    if data == "confirm_post":
        msg_id = context.user_data.get('msg_id')
        from_chat_id = context.user_data.get('chat_id')
        channel = context.user_data.get('selected_channel')

        if not msg_id or not from_chat_id or not channel:
            await query.edit_message_text("❌ حدث خطأ، لم أتمكن من العثور على الرسالة الأصلية.")
            return

        target_channels = CHANNELS if channel == "all" else [int(channel)]
        
        success = 0
        failed = 0
        failed_channels = []

        await query.edit_message_text("جاري النشر... ⏳")

        for channel_id in target_channels:
            try:
                await context.bot.copy_message(
                    chat_id=channel_id,
                    from_chat_id=from_chat_id,
                    message_id=msg_id
                )
                success += 1
            except Exception as e:
                failed += 1
                failed_channels.append(str(channel_id))
                logging.error(f"فشل النشر في {channel_id}: {e}")

        report = f"✅ تم النشر بنجاح في {success} قناة."
        if failed:
            report += f"\n❌ فشل النشر في {failed} قناة: {', '.join(failed_channels)}"

        await query.edit_message_text(report)
        context.user_data.clear()

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("channels", channels_cmd))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, receive_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("✅ البوت شغال ومستعد لتلقي الرسائل...")
    app.run_polling()

if __name__ == "__main__":
    main()
