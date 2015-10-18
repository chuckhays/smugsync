import traceback

import smugsync.Smugmug


def main():
    pass


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print 'Exception: ' + e.message
        tb = traceback.format_exc()
        print tb
