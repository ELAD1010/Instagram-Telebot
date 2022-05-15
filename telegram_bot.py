from enum import Enum

import yaml
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import Updater, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, Filters, \
    CallbackQueryHandler
from instagram_api import InstagramConnection
from instagram_private_api import ClientConnectionError, ClientLoginError, ClientError

user = {}
connections = {}
last_msg_id = 0

class ConversationOptions(Enum):
    Username =0,
    Password= 1,
    SuccessLogin = 2,
    Target = 3,
    TargetOptions = 4,
    Exit = 5,


class TargetOptions(str, Enum):
    ProfilePic = 'profile_pic',
    MediaDownload = 'download_media',
    Followers = 'user_followers'
    Followings = 'user_followings',
    UnFollowers = 'user_unfollowers',
    Unfollow_All = 'unfollow_all',
    Stories = 'user_stories',
    Close = 'close',


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(f'Hello {update.effective_user.full_name}\n'
                              f'Enter /login to connect to instagram')

def login(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Please Enter Your Username')

    return ConversationOptions.Username

def input_username(update: Update, context: CallbackContext) -> None:
    user[update.effective_user.full_name] = {}
    user[update.effective_user.full_name]['username'] = update.message.text
    update.message.reply_text('Please Enter Your Password')
    return ConversationOptions.Password


def input_password(update: Update, context: CallbackContext) -> None:
    user[update.effective_user.full_name]['password'] = update.message.text
    update.message.reply_text('Connecting To Instagram...')
    try:
        connection = InstagramConnection(user[update.effective_user.full_name])
        connections[update.effective_user.full_name] = connection
        button = [
                  [InlineKeyboardButton("Search User", callback_data='target')],
                  [InlineKeyboardButton("Logout", callback_data='logout')]
                 ]
        markup = InlineKeyboardMarkup(button)
        update.message.reply_text('Login Successful', reply_markup=markup)
        return ConversationOptions.SuccessLogin
    except ClientConnectionError:
        del user[update.effective_user.full_name]
        update.message.reply_text('Connecting To Instagram Failed\n'
                                  'To Connect again Enter /login')
        return ConversationHandler.END
    except ClientLoginError:
        del user[update.effective_user.full_name]
        update.message.reply_text('Incorrect Username Or Password\n'
                                  'To Connect again Enter /login')
        return ConversationHandler.END
    except ClientError as err:
        del user[update.effective_user.full_name]
        update.message.reply_text('Connecting To Instagram Failed\n'
                                  'Unable To Connect 2FA Users!')
        return ConversationHandler.END

def button_click_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    button_clicked = query.data
    if button_clicked == 'target':
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Enter Target Username')
        return ConversationOptions.Target
    elif button_clicked == 'logout':
        del user[update.effective_user.full_name]
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Logging out from Instagram Account...')
        connections[update.effective_user.full_name].logout()
        del connections[update.effective_user.full_name]
        context.bot.send_message(chat_id=update.effective_chat.id, text='Logged Out Successfully\n'
                                                                        'Please Type /login To Re-Login')
        return ConversationHandler.END


def input_target(update: Update, context: CallbackContext):
    target_username = update.message.text
    connection = connections[update.effective_user.full_name]
    try:
        target_info = connection.get_user(target_username).get('user')
        button = [
            [InlineKeyboardButton("Profile Picture", callback_data=TargetOptions.ProfilePic)],
            [InlineKeyboardButton("Download Media", callback_data=TargetOptions.MediaDownload)],
            [InlineKeyboardButton("User Followers", callback_data=TargetOptions.Followers)],
            [InlineKeyboardButton("User Followings", callback_data=TargetOptions.Followings)],
            [InlineKeyboardButton("User Unfollowers", callback_data=TargetOptions.UnFollowers)],
            [InlineKeyboardButton("User Stories", callback_data=TargetOptions.Stories)],
            [InlineKeyboardButton("Exit Target", callback_data=TargetOptions.Close)]
        ]
        markup = InlineKeyboardMarkup(button)
        update.message.reply_text(f'Target Profile:\n'
                                  f'Username: {target_info["username"]}\n'
                                  f'Private User: {target_info["is_private"]}\n'
                                  f'Posts: {target_info["media_count"]}\n'
                                  f'Followers: {target_info["follower_count"]}\n'
                                  f'Followings: {target_info["following_count"]}\n', reply_markup=markup)
        return ConversationOptions.TargetOptions
    except ClientError:
        update.message.reply_text('User Not Found!\n'
                                  'Please Enter Another Target')


def target_options_handler(update: Update, context: CallbackContext):
    global last_msg_id
    connection = connections[update.effective_user.full_name]
    query = update.callback_query
    button_clicked = query.data
    print(button_clicked)
    if button_clicked == TargetOptions.ProfilePic:
        profile_pic_url = connection.get_profile_pic()
        context.bot.send_photo(update.effective_chat.id,
                                 profile_pic_url)

    elif button_clicked == TargetOptions.MediaDownload:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Downloading User Media...')
        media_count, output_folder = connection.get_user_photos()
        context.bot.send_message(chat_id=update.effective_chat.id,
                               text=f'Downloaded {media_count} Posts \n'
                                     f'Saved In {output_folder} Folder')

    elif button_clicked == TargetOptions.Followers:
        followers = connection.get_followers()
        followers = [follower['username'] for follower in followers]
        if len(followers) > 200:
            followers = followers[0: 201]
        followers_str = '\n'.join(followers)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f'Followers List:\n'
                                      f'{followers_str}',)

    elif button_clicked == TargetOptions.Followings:
        followings = connection.get_followings()
        followings = [following['username'] for following in followings]
        followings_str = '\n'.join(followings)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f'Followings List:\n'
                                      f'{followings_str}',)

    elif button_clicked == TargetOptions.UnFollowers:
        unfollowers = connection.get_unfollowers()
        unfollowers = [unfollow['username'] for unfollow in unfollowers]
        unfollowers_str = '\n'.join(unfollowers)
        if len(unfollowers):
            msg = context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f'Unfollowers List({len(unfollowers)}):\n'
                                          f'{unfollowers_str}', reply_markup=
                                     InlineKeyboardMarkup([[InlineKeyboardButton("Unfollow All", callback_data=TargetOptions.Unfollow_All)]]))
            last_msg_id = msg["message_id"]
        else:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='No Unfollowers List!')

    elif button_clicked == TargetOptions.Unfollow_All:
        context.bot.delete_message(chat_id=update.effective_chat.id, message_id=last_msg_id)
        unfollowers = connection.get_unfollowers()
        connection.unfollow_all(unfollowers)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Unfollowing all succeeded!')


    elif button_clicked == TargetOptions.Stories:
        target_user, stories = connection.get_user_stories()
        if len(stories):
            media = []
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f'Stories Of {target_user}({len(stories)}):')
            for index, story in enumerate(stories):
                if story['type'] == 'image':
                    context.bot.send_photo(update.effective_chat.id,
                                           story['url'], f'Story #{index + 1}')
                else:
                    context.bot.send_video(chat_id=update.effective_chat.id,
                                           video=story['url'], caption=f'Story #{index + 1}')
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'user {target_user} has no stories')
    elif button_clicked == TargetOptions.Close:
        button = [
            [InlineKeyboardButton("Search User", callback_data='target')],
            [InlineKeyboardButton("Logout", callback_data='logout')]
        ]
        markup = InlineKeyboardMarkup(button)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Exit Target', reply_markup=markup)
        return ConversationOptions.SuccessLogin


def cancel(update: Update, context: CallbackContext):
    update.message.reply_text(
        f'Logout from {user[update.effective_user.full_name].username}')
    return ConversationHandler.END

with open('credentials.yaml') as file:
    bot_credentials = yaml.full_load(file)

TOKEN = bot_credentials.get('TOKEN')
print(TOKEN)

updater = Updater(TOKEN)

updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler('login', login)],
    states={
        ConversationOptions.Username: [MessageHandler(Filters.text, input_username)],
        ConversationOptions.Password: [MessageHandler(Filters.text, input_password)],
        ConversationOptions.SuccessLogin: [CallbackQueryHandler(button_click_handler)],
        ConversationOptions.Target: [MessageHandler(Filters.text, input_target)],
        ConversationOptions.TargetOptions: [CallbackQueryHandler(target_options_handler)]
    },
    fallbacks=[CommandHandler('logout', cancel)]
))


updater.start_polling()
updater.idle()
