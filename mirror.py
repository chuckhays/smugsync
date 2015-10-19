#!/usr/bin/python
import argparse
import traceback

from smugsync.Smugmug import Smugmug


def main():
    parser = argparse.ArgumentParser(description='SmugMug mirror script', fromfile_prefix_chars='@')
    parser.add_argument('-a', '--apikey', type=str, help='api key', required=True)
    parser.add_argument('-o', '--oauthsecret', type=str, help='oauth secret', required=True)
    parser.add_argument('-n', '--appname', type=str, help='app name', required=True)
    parser.add_argument('-p', '--path', type=str, help='output path', required=True)

    args = parser.parse_args()
    smugmug = Smugmug(api_key=args.apikey, oauth_secret=args.oauthsecret, app_name=args.appname)
    smugmug.authenticate()
    user = smugmug.get_authorized_user()
    albums = smugmug.get_albums(user)
    smugmug.mirror_albums(albums, args.path)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print 'Exception: ' + e.message
        tb = traceback.format_exc()
        print tb
