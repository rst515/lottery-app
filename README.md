# django-lottery-app
### Context
A village charity fundraises using a lottery bonus-ball game for local residents. A solution was required to make game administration simpler for the people running it. 

### How the game works
Players each have one or more bonus balls allocated.  They win if their number matches the drawn number for that week.

### What the app does
This Django web app enables a lottery bonus ball game coordinator to manage players, their allocated numbers and weekly draws for the game through a simple password-protected UI.

A cron job on an AWS EC2 instance runs weekly to execute a script that gets the bonus ball from the weekly National Lottery draw website and adds it to the database in the app.
The app provides a UI and coordinator(s) are emailed the result and winner following a weekly draw.

### Cron job details (on EC2 instance)
myscript.cron
```
# https://fauzan186.medium.com/how-to-add-django-custom-command-in-cron-57b5606f4ea4
# https://jainsaket-1994.medium.com/installing-crontab-on-amazon-linux-2023-ec2-98cf2708b171
#
# Run scheduled_task every sat at 8pm
0 20 * * 6 { printf "\%s: " "$(date "+\%F \%T")"; /home/ec2-user/venv/bin/python /home/ec2-user/wv-lottery/manage.py scheduled_task ; } >> /home/ec2-use>
#
# Test
#* * * * * { printf "\%s: " "$(date "+\%F \%T")"; /home/ec2-user/venv/bin/python --version ; } >> /home/ec2-user/test_cron.log 2>&1
```
Run this script

`$ crontab MyScript.cron`

Some useful commands

`$ crontab -l (Check current running cron job)`

`$ crontab -r (Remove cron job)`

### Running the project
1. [Clone the repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)
2. Set-up a python 3.9 [virtual environment](https://www.freecodecamp.org/news/how-to-setup-virtual-environments-in-python/#:~:text=How%20to%20Install%20a%20Virtual%20Environment%20using%20Venv) 
3. Install dependencies from the project root with `pip install -r requirements.txt`
4. Create the local `db.sqlite3` database with `python manage.py migrate`
5. Create a superuser with `python manage.py createsuperuser`
6. Run the web interface with `python manage.py runserver` and log-in with the user account you created in the previous step
7You may also use the admin interface to create other app users: append `/admin` to the url in the browser to access the admin site

Optionally: 
1. Deploy the cron script above to an AWS EC2 instance (charges may apply) with a copy of the repo code, or alternatively manually enter the draw result in the app (this option does not provide email notifications).
2. The helper script `create_balls.py` can be used to create bonus balls with `python manage.py shell < create_balls.py`
