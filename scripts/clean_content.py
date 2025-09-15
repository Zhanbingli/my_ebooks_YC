#!/usr/bin/env python3
import os

CONTENT_DIR = 'content'

def main():
    if not os.path.isdir(CONTENT_DIR):
        print('No content directory found.')
        return
    removed = 0
    for name in os.listdir(CONTENT_DIR):
        if not name.endswith('.md'):
            continue
        if name.startswith('000-introduction'):
            continue
        path = os.path.join(CONTENT_DIR, name)
        os.remove(path)
        removed += 1
    print(f'Removed {removed} chapter files (kept 000-introduction).')

if __name__ == '__main__':
    main()

