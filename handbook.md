# Handbook
Welcome to the official acmOpportunities handbook! Here will be a detailed tutorial on how to set up all the technical aspects.

## Step 1 - Install Python & Fork Repository
Make sure to install Python before we continue [here!](https://www.python.org/downloads/).

Once you're done, go ahead and fork this repository.

## Step 2 - Setting up
You have **MANY** environment variables to set up. Let's go through each one and discuss how to get the information for them!

### Job/Internship URL's
Here, we have the following variables:
```py
LINKEDIN_URL=""
LINKEDIN_INTERN_URL=""
GH_INTERN24_URL="https://github.com/pittcsc/Summer2024-Internships"
```
As you can see, the `GH_INTERN24_URL` is already populated for you.
To populate the LinkedIn URL's please go ahead and search up your type of job.
In this example, we will search up `Software Engineer` for `LINKEDIN_URL` and `Software Engineer Intern` for `LINKEDIN_INTERN_URL`.

Go ahead and copy the link at the top and paste it into the variable names.
![Alt text](image.png)


### PaLM
Here, we have the following variable:
```py
PALM_API_KEY=""
```
If you haven't already, please sign up for access for [MakerSuite](https://makersuite.google.com/).

Click this button on the left once you're ready.
![Alt text](image-1.png)

Now, click the left button called `Create API key in new project` and **copy** you key.
![Alt text](image-2.png)

Paste your key into the **PALM_API_KEY** enviornment variable.

### Prompt Path
Here, we have the following variable:
```py
PROMPTS_PATH=""
```
Depending on your bot's purpose, you might want to send notifications related to various fields such as Computer Science, Health, Arts, Cybersecurity, and more. To do this, please specify the file path relative to the `PROMPTS_PATH`` variable.

We offer the following:
```
**Computer Science** - /prompts/cs.json
**CyberSecurity** - /prompts/cybersecurity.json
```

**If you do not see your type, please create an issue and we will add it in.**

### Message Path
Here, we have the following variable:
```py
MESSAGE_PATH=""
```
You are able to customize the styling of your message!
The default styling is the following:
`[**{company}**]({link}): {title} `@{location}`!`
![Alt text](image-3.png)

Go ahead and customize it how you like in `./msg/message.json`.
**If you would like the default styling, you can leave that file untouched.**

### Discord Bot
Here, we have the following variable:
```py
DISCORD_WEBHOOK=""
```
Now that we've taken care of the basic setup, it's time to configure our bot. In this project, we utilize Discord webhooks, which serve as a means of communication, allowing various programs to seamlessly transmit messages within a Discord chat. This streamlines the process of receiving updates and notifications from multiple sources, all conveniently located in one central location.

1. Click **Server Settings**
![Alt text](image-4.png)

2. Click **Integrations** 
![Alt text](image-5.png)

3. Click **Create a Webhook** 
![Alt text](image-6.png)

4. Create a new webhook and **copy the url**
![Alt text](image-7.png)
*If necessary, you have the flexibility to adjust the channel where your Discord bot sends its messages to suit your preferences.*

Add that link into the `DISCORD_WEBHOOK` enviornment variable.

### Setting up Database Table
Here, we have the following variables:
```py
DB_URI=""
DB_TABLE="opportunities_table"
```

As you can see, your database table name is already given to you. You can change it to however you like.

To set up your table in your database, please refer to the [follow documentation](https://www.elephantsql.com/docs/index.html) for it. **Do not create a table, we will do that here.**

After you've set yours up, please copy paste the URL into the `DB_URI`.
![Alt text](image-8.png)

## Step 3 - Install Dependencies
Pip install the dependencies of main.py using `pip install -r requirements.txt`.

## Step 4 - Create Table in your Database
To create the table, write `python ./main --create` **once** in the terminal.
![Alt text](image-9.png)

If you go back to your database and click **Browser** and **Table Queries** you should see your newly made table.
![Alt text](image-11.png)

## Step 5 - Final Steps
Congratulations! The discord bot will now send in opportunities **every other day**.

**If you would like to test ir right now and run the program manually, write `python ./main.py --days-needed 2` in the terminal.**



