# Cool-lil-android-game-hub-yay (single-file version)

Only TWO files matter:

    main.py          <- the whole game hub (menu + Snake + 2048 + Temple Runner + Flappy Bounce)
    buildozer.spec   <- settings for making the Android APK

## 1. Play it on your computer

    cd ~/Cool-lil-android-game-hub-yay
    python3 main.py

Keys: arrows (or WASD) = move, SPACE/ENTER = select, ESC = back.
Mouse: click the on-screen buttons, or click-and-drag to swipe.

## 2. Save your work (your Live USB forgets everything on shutdown!)

First time only:

    git config --global user.name "Your Name"
    git config --global user.email "you@example.com"
    git init
    git add .
    git commit -m "My game hub"
    git branch -M main
    git remote add origin https://github.com/YOUR-USERNAME/Cool-lil-android-game-hub-yay.git
    git push -u origin main

GitHub asks for a password: paste a Personal Access Token
(GitHub -> Settings -> Developer settings -> Personal access tokens).

After every work session:

    git add .
    git commit -m "what I changed"
    git push

## 3. Build the Android APK

See the chat message for the exact copy-paste commands.
