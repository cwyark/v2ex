import os

from google.appengine.ext import webapp

from . import main, topic, mail, avatar, template, feed, member, place, misc, notes, backstage, money, my, t, images, favorite, queue, sso, notifications, page, blog, xmpp, api, css

config = {}
config['webapp2_extras.i18n'] = {
    'translations_path': 'locale',
}
config['webapp2_extras.jinja2'] = {
    'environment_args': {
        'extensions': ['jinja2.ext.i18n']
    }
}

routes = [
    ('/', main.HomeHandler),
    ('/planes/?', main.PlanesHandler),
    ('/recent', main.RecentHandler),
    ('/signin', main.SigninHandler),
    ('/signup', main.SignupHandler),
    ('/signout', main.SignoutHandler),
    ('/forgot', main.ForgotHandler),
    ('/reset/([0-9]+)', main.PasswordResetHandler),
    ('/go/([a-zA-Z0-9]+)/graph', main.NodeGraphHandler),
    ('/go/([a-zA-Z0-9]+)', main.NodeHandler),
    ('/n/([a-zA-Z0-9]+).json', main.NodeApiHandler),
    ('/q/(.*)', main.SearchHandler),
    ('/_dispatcher', main.DispatcherHandler),
    ('/changes', main.ChangesHandler),
    ('/(.*)', main.RouterHandler),

    ('/new/(.*)', topic.NewTopicHandler),
    ('/t/([0-9]+)', topic.TopicHandler),
    ('/t/([0-9]+).txt', topic.TopicPlainTextHandler),
    ('/edit/topic/([0-9]+)', topic.TopicEditHandler),
    ('/delete/topic/([0-9]+)', topic.TopicDeleteHandler),
    ('/index/topic/([0-9]+)', topic.TopicIndexHandler),
    ('/edit/reply/([0-9]+)', topic.ReplyEditHandler),
    ('/hit/topic/(.*)', topic.TopicHitHandler),
    ('/hit/page/(.*)', topic.PageHitHandler),

    mail.MailHandler.mapping(),

    ('/avatar/([0-9]+)/(large|normal|mini)', avatar.AvatarHandler),
    ('/navatar/([0-9]+)/(large|normal|mini)', avatar.NodeAvatarHandler),

    ('/my/nodes', template.MyNodesHandler),

    ('/index.xml', feed.FeedHomeHandler),
    ('/read.xml', feed.FeedReadHandler),
    ('/feed/v2ex.rss', feed.FeedHomeHandler),
    ('/feed/([0-9a-zA-Z\-\_]+).xml', feed.FeedNodeHandler),

    ('/member/([a-z0-9A-Z\_\-]+)', member.MemberHandler),
    ('/member/([a-z0-9A-Z\_\-]+).json', member.MemberApiHandler),
    ('/settings', member.SettingsHandler),
    ('/settings/password', member.SettingsPasswordHandler),
    ('/settings/avatar', member.SettingsAvatarHandler),
    ('/block/(.*)', member.MemberBlockHandler),
    ('/unblock/(.*)', member.MemberUnblockHandler),

    ('/place/([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})', place.PlaceHandler),
    ('/remove/place_message/(.*)', place.PlaceMessageRemoveHandler),

    ('/time/?', misc.WorldClockHandler),
    ('/(md5|sha1)/?', misc.MD5Handler),
    ('/bfbcs/poke/(ps3|360|pc)/(.*)', misc.BFBCSPokeHandler),

    ('/notes', notes.NotesHomeHandler),
    ('/notes/new', notes.NotesNewHandler),
    ('/notes/([0-9]+)', notes.NotesItemHandler),
    ('/notes/([0-9]+)/erase', notes.NotesItemEraseHandler),
    ('/notes/([0-9]+)/edit', notes.NotesItemEditHandler),

    ('/backstage', backstage.BackstageHomeHandler),
    ('/backstage/new/minisite', backstage.BackstageNewMinisiteHandler),
    ('/backstage/minisite/(.*)', backstage.BackstageMinisiteHandler),
    ('/backstage/remove/minisite/(.*)', backstage.BackstageRemoveMinisiteHandler),
    ('/backstage/new/page/(.*)', backstage.BackstageNewPageHandler),
    ('/backstage/page/(.*)', backstage.BackstagePageHandler),
    ('/backstage/remove/page/(.*)', backstage.BackstageRemovePageHandler),
    ('/backstage/new/section', backstage.BackstageNewSectionHandler),
    ('/backstage/section/(.*)', backstage.BackstageSectionHandler),
    ('/backstage/new/node/(.*)', backstage.BackstageNewNodeHandler),
    ('/backstage/node/([a-z0-9A-Z]+)', backstage.BackstageNodeHandler),
    ('/backstage/node/([a-z0-9A-Z]+)/avatar', backstage.BackstageNodeAvatarHandler),
    ('/backstage/remove/reply/(.*)', backstage.BackstageRemoveReplyHandler),
    ('/backstage/tidy/reply/([0-9]+)', backstage.BackstageTidyReplyHandler),
    ('/backstage/tidy/topic/([0-9]+)', backstage.BackstageTidyTopicHandler),
    ('/backstage/deactivate/user/(.*)', backstage.BackstageDeactivateUserHandler),
    ('/backstage/move/topic/(.*)', backstage.BackstageMoveTopicHandler),
    ('/backstage/site', backstage.BackstageSiteHandler),
    ('/backstage/topic', backstage.BackstageTopicHandler),
    ('/backstage/remove/mc', backstage.BackstageRemoveMemcacheHandler),
    ('/backstage/member/(.*)', backstage.BackstageMemberHandler),
    ('/backstage/members', backstage.BackstageMembersHandler),
    ('/backstage/remove/notification/(.*)', backstage.BackstageRemoveNotificationHandler),

    ('/money/dashboard/?', money.MoneyDashboardHandler),

    ('/my/nodes', my.MyNodesHandler),
    ('/my/topics', my.MyTopicsHandler),
    ('/my/following', my.MyFollowingHandler),

    ('/twitter/?', t.TwitterHomeHandler),
    ('/twitter/mentions/?', t.TwitterMentionsHandler),
    ('/twitter/inbox/?', t.TwitterDMInboxHandler),
    ('/twitter/user/([a-zA-Z0-9\_]+)', t.TwitterUserTimelineHandler),
    ('/twitter/link', t.TwitterLinkHandler),
    ('/twitter/unlink', t.TwitterUnlinkHandler),
    ('/twitter/oauth', t.TwitterCallbackHandler),
    ('/twitter/tweet', t.TwitterTweetHandler),
    ('/twitter/api/?', t.TwitterApiCheatSheetHandler),
    
    ('/images/upload', images.ImagesUploadHandler),
    ('/images/upload/rules', images.ImagesUploadRulesHandler),
    ('/images/?', images.ImagesHomeHandler),

    ('/favorite/node/([a-zA-Z0-9]+)', favorite.FavoriteNodeHandler),
    ('/unfavorite/node/([a-zA-Z0-9]+)', favorite.UnfavoriteNodeHandler),
    ('/favorite/topic/([0-9]+)', favorite.FavoriteTopicHandler),
    ('/unfavorite/topic/([0-9]+)', favorite.UnfavoriteTopicHandler),
    ('/follow/([0-9]+)', favorite.FollowMemberHandler),
    ('/unfollow/([0-9]+)', favorite.UnfollowMemberHandler),

    ('/add/star/topic/(.*)', queue.AddStarTopicHandler),
    ('/minus/star/topic/(.*)', queue.MinusStarTopicHandler),

    ('/sso/v0', sso.SSOV0Handler),
    ('/sso/x0', sso.SSOX0Handler),

    ('/notifications/?', notifications.NotificationsHandler),
    ('/notifications/check/(.+)', notifications.NotificationsCheckHandler),
    ('/notifications/reply/(.+)', notifications.NotificationsReplyHandler),
    ('/notifications/topic/(.+)', notifications.NotificationsTopicHandler),
    ('/n/([a-z0-9]+).xml', notifications.NotificationsFeedHandler),

    ('/about', page.AboutHandler),
    ('/faq', page.FAQHandler),
    ('/mission', page.MissionHandler),
    ('/advertise', page.AdvertiseHandler),
    ('/advertisers', page.AdvertisersHandler),

    ('/blog/([a-z0-9A-Z\_\-]+)', blog.BlogHandler),
    ('/entry/([0-9]+)', blog.BlogEntryHandler),

    ('/_ah/xmpp/message/chat/', xmpp.XMPPHandler),

    ('/api/site/stats.json', api.SiteStatsHandler),
    ('/api/site/info.json', api.SiteInfoHandler),
    ('/api/nodes/all.json', api.NodesAllHandler),
    ('/api/nodes/show.json', api.NodesShowHandler),
    ('/api/topics/latest.json', api.TopicsLatestHandler),
    ('/api/topics/show.json', api.TopicsShowHandler),
    ('/api/topics/create.json', api.TopicsCreateHandler),
    ('/api/replies/show.json', api.RepliesShowHandler),
    ('/api/members/show.json', api.MembersShowHandler),
    ('/api/currency.json', api.CurrencyHandler),


    ('/css/([a-zA-Z0-9]+).css', css.CSSHandler),
]



debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

application = webapp.WSGIApplication(config = config, debug = debug, routes = routes)
