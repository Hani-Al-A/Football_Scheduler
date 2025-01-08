Distinctiveness and Complexity:
My project is distinct to all the other projects done in this course as it handles soccer/football schedules for professional clubs at the highest level of the sport, allowing coaches to plan ahead for their squad and also keeping players informed about whats upcoming in their week. One reason this is a more complex project than the rest is because it pulls information out of a complex and large API that stores alot of data about football and its players, matches, clubs etc. . Another reason is that it uses djangos email module to allow coaches to send reminders to selected players in their squad with the click of a button. One more reason it is more complex is that it uses user-friendly animations which make the user understand the website better and interact with it more and using a simple design the user can easily understand what to press on. The website also makes use of youtubes embed feature to allow coaches to add video examples of training drills they want to implement for their squad. One more it is complex is that it uses sophisticated HTML manipulation to change the look of the default HTML calendar from the calendar library. The final reason for it passing the complexity requirement of this project is that it is a timezone aware website, using JavaScript to detect user timezones and change all timings in their calendar to the correct time for that country, which is important as football players are constantly traveling through different timezones and having the correct timing will help them be on time for important scheduled events.


Files:

    training folder/app:

        views.py:
        contains the functions and views that control the server on the back end

        urls.py:
        contains the routes and urls for each page and the views they should call should the urls be called

        context_processors.py:
        contains a current_date function that calls datetime.datetime.now() so that when the schedule button is pressed on it will immediately take the user to the current months schedule by calling that function and taking the month and year into the url

        admin.py:
        contains the code that allows admins to modify the database from the admin page

        settings.py:
        includes additions to allow for the use of the django email module

        static folder:
        contains the javascript and css files needed for each page to look and function the way they are supposed to, providing users a good user interface

        templates folder:
        contains all the html files for every page for the website
    


How to run the application:

Simply run the server in a django project using terminal, and then open the development server at the specified port, and start using the application by creating an account as either a player or coach.


Additional Information:
This project is aimed at an audience of professional football players and coaches, and helps them easily produce a routine and schedule while also having the necessary security features preventing other clubs from viewing calendars that are not theirs. Upon registering, you will find that the leagues, clubs, and players/coaches are all real and taken from an API. If you are logged in as a coach you will be able to "sync real calendar" and load all the real-life matches from the current and previous season for that coaches club. 



