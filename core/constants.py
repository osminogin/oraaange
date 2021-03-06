from itertools import chain

USER_ABUSE_MODERATOR = 'User abuse moderator'
AD_ABUSE_MODERATOR = 'Ad abuse moderator'
ABUSE_MODERATOR = 'Abuse moderator'
FEEDBACK_MODERATOR = 'Feedback moderator'
MODERATOR = 'Moderator'

GROUPS = [
    USER_ABUSE_MODERATOR,
    AD_ABUSE_MODERATOR,
    ABUSE_MODERATOR,
    FEEDBACK_MODERATOR,
    MODERATOR,
]

USER_ABUSE_MODERATOR_PERMISSIONS = [
    'view_user', 'change_user', 'view_userabuse', 'change_userabuse'
]

AD_ABUSE_MODERATOR_PERMISSIONS = [
    'view_ad', 'change_ad', 'view_adabuse', 'change_adabuse'
]

FEEDBACK_MODERATOR_PERMISSIONS = ['view_feedback']

PERMISSIONS_MAP = {
    USER_ABUSE_MODERATOR: USER_ABUSE_MODERATOR_PERMISSIONS,
    AD_ABUSE_MODERATOR: AD_ABUSE_MODERATOR_PERMISSIONS,
    ABUSE_MODERATOR: chain(
        USER_ABUSE_MODERATOR_PERMISSIONS, AD_ABUSE_MODERATOR_PERMISSIONS
    ),
    FEEDBACK_MODERATOR: FEEDBACK_MODERATOR_PERMISSIONS,
    MODERATOR: chain(
        USER_ABUSE_MODERATOR_PERMISSIONS,
        AD_ABUSE_MODERATOR_PERMISSIONS,
        FEEDBACK_MODERATOR_PERMISSIONS
    )
}

MULTIMEDIA_FILE_TYPES = ['image', 'video', 'audio', 'portfolio', 'avatar', 'screenshot']

# Event types
EVENT_NEW_CHAT = 'NEW_CHAT'
EVENT_CHAT_DELETE = 'CHAT_DELETE'
EVENT_NEW_MESSAGE = 'NEW_MESSAGE'
EVENT_MESSAGE_STATUS = 'MESSAGE_STATUS'
EVENT_MESSAGE_DELETE = 'MESSAGE_DELETE'
EVENT_UPDATES = 'UPDATES'
EVENT_HARAKIRI = 'HARAKIRI'     # NotImplementedError
