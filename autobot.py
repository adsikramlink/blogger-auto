name: Auto Post Blogger

on:
  schedule:
    # Jadwal 5x Sehari (Waktu UTC = WIB - 7 Jam)
    # 07:00 WIB = 00:00 UTC
    # 10:00 WIB = 03:00 UTC
    # 13:00 WIB = 06:00 UTC
    # 16:00 WIB = 09:00 UTC
    # 20:00 WIB = 13:00 UTC
    - cron: '0 0,3,6,9,13 * * *'
  workflow_dispatch: # Tombol manual

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install Dependencies
      run: |
        python -m pip install --upgrade pip
        pip install requests google-generativeai google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

    - name: Run AutoBot
      env:
        GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        BLOGGER_CLIENT_ID: ${{ secrets.BLOGGER_CLIENT_ID }}
        BLOGGER_CLIENT_SECRET: ${{ secrets.BLOGGER_CLIENT_SECRET }}
        BLOGGER_REFRESH_TOKEN: ${{ secrets.BLOGGER_REFRESH_TOKEN }}
        BLOGGER_ID: ${{ secrets.BLOGGER_ID }}
        IMGBB_API_KEY: ${{ secrets.IMGBB_API_KEY }}
      run: python autobot.py
