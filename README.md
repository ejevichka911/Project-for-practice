# Project-for-practice
This Telegram bot is designed for convenient media content management - movies, TV series, and books. It helps users organize their collections, take notes, save favorites, and get recommendations in the dedicated "Recommendations" section through a flexible filtering system.

The bot features an intuitive button-based menu that allows browsing available content lists, viewing details (release year, genre, rating, etc.), and saving personal notes. Users can add their favorite movies, series, and books to a separate collection for quick access. My bot also includes a recommendations feature.

Movies and TV series can be filtered by genre, country, year, rating, and age restrictions. Books can additionally be sorted by publisher and series availability. All favorited items are available in a dedicated "Favorites" section with quick navigation and collection management options.

Notes can be added, edited, and deleted, which is convenient for keeping track of watched or read content. The bot supports pagination for easy browsing of large lists and stores data in JSON files and an SQLite database.

Technically, the bot is written in Python using the python-telegram-bot library, operates on a Finite State Machine (FSM) for dialogue management, and is easily extensible. Future enhancements could include integration with databases (IMDb, Kinopoisk), an advanced machine learning-based recommendation system, ratings, and social features including recommendation sharing between users.

To run the bot, you'll need Python 3.7+, installation of dependencies (pip install python-telegram-bot), and bot token configuration. Suitable for personal use as a media organizer, it also has potential for development into a full-fledged recommendation service, media content management system, and social platform for movie and book enthusiasts.
