from telegram import InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler
from time import sleep

from bot import download_dict, dispatcher, download_dict_lock, DOWNLOAD_DIR, QB_SEED, SUDO_USERS, OWNER_ID
from bot.helper.ext_utils.fs_utils import clean_download
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import sendMessage, sendMarkup
from bot.helper.ext_utils.bot_utils import getDownloadByGid, MirrorStatus, getAllDownload
from bot.helper.telegram_helper import button_build


def cancel_mirror(update, context):
    args = update.message.text.split(" ", maxsplit=1)
    user_id = update.message.from_user.id
    if len(args) > 1:
        gid = args[1]
        dl = getDownloadByGid(gid)
        if not dl:
            return sendMessage(f"ℹ️ GID: <code>{gid}</code> Tidak Ditemukan.", context.bot, update.message)
    elif update.message.reply_to_message:
        mirror_message = update.message.reply_to_message
        with download_dict_lock:
            keys = list(download_dict.keys())
            try:
                dl = download_dict[mirror_message.message_id]
            except:
                dl = None
        if not dl:
            return sendMessage(f"ℹ️ This is not an active task!", context.bot, update.message)
    elif len(args) == 1:
        msg = f"ℹ️ Ketik <code>/{BotCommands.CancelMirror} Download ID</code> untuk cancel mirror!"
        return sendMessage(msg, context.bot, update.message)

    if OWNER_ID == user_id or dl.message.from_user.id == user_id or user_id in SUDO_USERS:
        pass
    else:
        return sendMessage("This task is not for you!", context.bot, update.message)

    if dl.status() == MirrorStatus.STATUS_ARCHIVING:
        sendMessage("⚠️ Archival in Progress, You Can't Cancel It.", context.bot, update.message)
    elif dl.status() == MirrorStatus.STATUS_EXTRACTING:
        sendMessage("⚠️ Extract in Progress, You Can't Cancel It.", context.bot, update.message)
    elif dl.status() == MirrorStatus.STATUS_SPLITTING:
        sendMessage("⚠️ Split in Progress, You Can't Cancel It.", context.bot, update.message)
    else:
        dl.download().cancel_download()

def cancel_all(status):
    gid = ''
    while True:
        dl = getAllDownload(status)
        if dl:
            if dl.gid() != gid:
                gid = dl.gid()
                dl.download().cancel_download()
                sleep(1)
        else:
            break

def cancell_all_buttons(update, context):
    buttons = button_build.ButtonMaker()
    buttons.sbutton("Downloading", "canall down")
    buttons.sbutton("Uploading", "canall up")
    if QB_SEED:
        buttons.sbutton("Seeding", "canall seed")
    buttons.sbutton("Cloning", "canall clone")
    buttons.sbutton("All", "canall all")
    button = InlineKeyboardMarkup(buttons.build_menu(2))
    sendMarkup('Choose tasks to cancel.', context.bot, update.message, button)

def cancel_all_update(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    data = data.split(" ")
    if CustomFilters._owner_query(user_id):
        query.answer()
        query.message.delete()
        cancel_all(data[1])
    else:
        query.answer(text="You don't have permission to use these buttons!", show_alert=True)



cancel_mirror_handler = CommandHandler(BotCommands.CancelMirror, cancel_mirror,
                                       filters=(CustomFilters.authorized_chat | CustomFilters.authorized_user), run_async=True)

cancel_all_handler = CommandHandler(BotCommands.CancelAllCommand, cancell_all_buttons,
                                    filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)

cancel_all_buttons_handler = CallbackQueryHandler(cancel_all_update, pattern="canall", run_async=True)

dispatcher.add_handler(cancel_all_handler)
dispatcher.add_handler(cancel_mirror_handler)
dispatcher.add_handler(cancel_all_buttons_handler)
