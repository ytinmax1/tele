import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from config import BOT_TOKEN, ADMIN_IDS, CHANNELS

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

async def check_admin(update: Update):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        if update.message:
            await update.message.reply_text("❌ مش مصرح لك تستخدم البوت ده.")
        elif update.callback_query:
            await update.callback_query.answer("❌ مش مصرح لك.", show_alert=True)
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update): return
    await update.message.reply_text(
        "🤖 أهلاً بك في نظام النشر الاحترافي!\n\n"
        "ابعت أي رسالة (نص، صورة، فيديو، ملف، استطلاع رأي، إلخ..)\n"
        "وهتظهر لك لوحة تحكم تختار منها القنوات اللي عايز تنشر فيها بكل سهولة.\n\n"
        "/channels - عشان تشوف وتحدث القنوات المتصلة"
    )

async def _get_channel_names(context: ContextTypes.DEFAULT_TYPE):
    if "channel_names" not in context.bot_data:
        context.bot_data["channel_names"] = {}
    
    for ch in CHANNELS:
        if ch not in context.bot_data["channel_names"]:
            try:
                chat = await context.bot.get_chat(ch)
                context.bot_data["channel_names"][ch] = chat.title
            except Exception as e:
                logging.error(f"Failed to get channel name for {ch}: {e}")
                context.bot_data["channel_names"][ch] = f"قناة {ch}"
    return context.bot_data["channel_names"]

async def channels_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update): return
    
    if not CHANNELS:
        await update.message.reply_text("❌ مفيش أي قنوات متصلة بالبوت حالياً.")
        return
        
    await update.message.reply_text("جاري جلب أسماء القنوات... ⏳")
    names = await _get_channel_names(context)
    
    text = "📢 القنوات المتصلة بنظام النشر:\n\n"
    for i, ch in enumerate(CHANNELS, 1):
        text += f"{i}. {names.get(ch, str(ch))}\n"
    await update.message.reply_text(text)

def _build_keyboard(context: ContextTypes.DEFAULT_TYPE):
    selected = context.user_data.get('selected_channels', set())
    names = context.bot_data.get('channel_names', {})
    
    keyboard = []
    for ch in CHANNELS:
        is_selected = ch in selected
        mark = "✅" if is_selected else "❌"
        ch_name = names.get(ch, f"قناة {ch}")
        keyboard.append([InlineKeyboardButton(f"{mark} {ch_name}", callback_data=f"toggle_{ch}")])
    
    # Control buttons
    controls = []
    if len(selected) < len(CHANNELS):
        controls.append(InlineKeyboardButton("✅ تحديد الكل", callback_data="select_all"))
    if len(selected) > 0:
        controls.append(InlineKeyboardButton("❌ إلغاء تحديد الكل", callback_data="deselect_all"))
    
    if controls:
        keyboard.append(controls)
        
    if len(selected) > 0:
        keyboard.append([InlineKeyboardButton(f"🚀 إرسال للقنوات المحددة ({len(selected)})", callback_data="confirm_post")])
        
    keyboard.append([InlineKeyboardButton("🗑️ إلغاء العملية", callback_data="cancel")])
    
    return InlineKeyboardMarkup(keyboard)

async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update): return

    if not CHANNELS:
        await update.message.reply_text("❌ مفيش قنوات متصلة عشان أنشر فيها. ضيف قنوات في ملف الإعدادات الأول.")
        return

    # Ensure names are cached
    await _get_channel_names(context)

    # Store message details and initialize empty selection
    context.user_data['msg_id'] = update.message.message_id
    context.user_data['chat_id'] = update.effective_chat.id
    context.user_data['selected_channels'] = set()

    reply_markup = _build_keyboard(context)
    await update.message.reply_text(
        "لوحة التحكم:\nاختر القنوات التي تريد نشر الرسالة فيها:",
        reply_markup=reply_markup,
        reply_to_message_id=update.message.message_id
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update): return
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "cancel":
        await query.edit_message_text("تم الإلغاء وحذف العملية. ❌")
        context.user_data.clear()
        return

    if data.startswith("toggle_"):
        ch = int(data.split("_")[1])
        selected = context.user_data.get('selected_channels', set())
        if ch in selected:
            selected.remove(ch)
        else:
            selected.add(ch)
        context.user_data['selected_channels'] = selected
        
        await query.edit_message_reply_markup(reply_markup=_build_keyboard(context))
        return

    if data == "select_all":
        context.user_data['selected_channels'] = set(CHANNELS)
        await query.edit_message_reply_markup(reply_markup=_build_keyboard(context))
        return

    if data == "deselect_all":
        context.user_data['selected_channels'] = set()
        await query.edit_message_reply_markup(reply_markup=_build_keyboard(context))
        return

    if data == "confirm_post":
        msg_id = context.user_data.get('msg_id')
        from_chat_id = context.user_data.get('chat_id')
        target_channels = context.user_data.get('selected_channels', set())

        if not msg_id or not from_chat_id or not target_channels:
            await query.edit_message_text("❌ حدث خطأ أو لم يتم تحديد قنوات.")
            return

        success = 0
        failed = 0
        failed_channels = []
        names = context.bot_data.get('channel_names', {})

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
                ch_name = names.get(channel_id, str(channel_id))
                failed_channels.append(ch_name)
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
