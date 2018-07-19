from unsplash.api import Api
from unsplash.auth import Auth
import praw
from time import sleep
from config import *
import sqlite3

# Login into reddit function
def auth_reddit():
    try:
        reddit = praw.Reddit(
            client_id = REDDIT_CLIENT_ID,
            client_secret = REDDIT_CLIENT_SECRET,
            password = REDDIT_PASSWORD,
            user_agent = REDDIT_USER_AGENT,
            username = REDDIT_USERNAME)
    except Exception as e:
        print(e)
        sleep(60)
    print('Logged in into reddit')
    return reddit

# Login into unsplash function
def auth_unsplash():
    auth = Auth(UNSPLASH_CLIENT_ID, UNSPLASH_CLIENT_SECRET, UNSPLASH_REDIRECT_URI, code=UNSPLASH_CODE)
    api = Api(auth)
    print('Logged in into unsplash')
    return api

# Main function that posts random photo to the specified subreddit every 5 hours
def post_random_photo(reddit, api):
    # Connect into the database
    conn = sqlite3.connect(SQLITE_FILE)
    c = conn.cursor()
    # Create a table and a column if they do not exist
    c.execute('CREATE TABLE IF NOT EXISTS {tn} ({cn} {ct})' \
              .format(tn = TABLE_NAME, cn = COLUMN_NAME, ct = COLUMN_TYPE))
    # Get a random photo from unsplash
    random_photo = api.photo.random()
    # Get the photo ID
    photo_id = random_photo[0].id
    # Check if the random photo has been posted by the bot before
    c.execute('SELECT ' + COLUMN_NAME + ' FROM ' + TABLE_NAME + ' WHERE ' + COLUMN_NAME + ' = (?)', (photo_id,))
    # If it has not been posted before
    if c.fetchone() == None:
        # Get its properties
        link = random_photo[0].links.html
        url = random_photo[0].urls.raw
        description = random_photo[0].description
        op_username = random_photo[0].user.username
        op_name = random_photo[0].user.name
        op_website = '[- Personal Website]({}) '.format(random_photo[0].user.portfolio_url)
        op_unsplash = '[Unsplash](https://unsplash.com/@{}) '.format(random_photo[0].user.username)
        op_instagram = '[- Instagram](https://www.instagram.com/{}) '.format(random_photo[0].user.instagram_username)
        op_twitter =  '[- Twitter](https://twitter.com/{})'.format(random_photo[0].user.twitter_username)
        # If some of the properties are None then change them to an empty string
        if description == None:
            description = 'A photo'
        if random_photo[0].user.portfolio_url == None:
            op_website = ''
        if random_photo[0].user.instagram_username == None:
            op_instagram = ''
        if random_photo[0].user.twitter_username == None:
            op_twitter = ''
        # Submission text
        submission_title = '{} by {} (@{}) on Unsplash'.format(description, op_name, op_username)
        # Comment text
        submission_comment_body = '[View the photo on Unsplash.com]({})\n\nFind the photographer on: {} {} {} {}'\
        .format(link, op_unsplash, op_website, op_instagram, op_twitter)
        # Create a new submission
        new_submission = reddit.subreddit(REDDIT_SUBREDDIT_NAME).submit(submission_title, url = url, send_replies = False)
        # Create a new comment to that submission
        new_comment = new_submission.reply(submission_comment_body)
        # Insert the photo ID to the database
        c.execute('INSERT OR IGNORE INTO ' + TABLE_NAME + ' (' + COLUMN_NAME + ') ' + 'VALUES (?)', (str(photo_id),))
        conn.commit()
        print('Created a new submission ({}) and a new comment ({})'.format(new_submission.id, new_comment.id))
        conn.close()
        # Sleep for 5 hours
        sleep(18000)

# Main code block
reddit = auth_reddit()
api = auth_unsplash()
while True:
    post_random_photo(reddit, api)