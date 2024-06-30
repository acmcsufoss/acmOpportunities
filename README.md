# [❗UNDER CONSTRUCTION❗] acmOpportunities

## acmOpportunities is currently under construction for V.2. due to recent unfortunate [ElephantSQL changes](https://www.elephantsql.com/blog/end-of-life-announcement.html).

The acmOpportunities Discord Bot is a tool designed for students in our club. This bot keeps developers informed about the latest job opportunities in the industry by sending job listings directly to the ACM Discord server.

## Key features

- **Stay informed**: Filtered by AI, acmOpportunities keeps up-to-date with the latest SWE job opportunities near Fullerton, CA without having to manually search for them.
- **Seamless integration**: With the integration of PostgreSQL and Discord, acmOpportunities provides a seamless user experience.

## Usage

1. Install [Python](https://www.python.org/downloads/).
2. Pip install the dependencies of main.py using `pip install -r requirements.txt`.
3. Set the required environment variables located in `.env.example`.
4. To create the table, write `python ./main --create` once.
5. To run the program manually, write `python ./main.py --days-needed 2`.

> ℹ️ **PLEASE NOTE THE FOLLOWING** ℹ️<br/>
> Please adjust the amount of days needed
> when using the `--days-needed` command.<br/> **Additionally**, please update the workflow in
> `./github/workflows` to correspond to the wanted amount of days.

## Develop

- If you don't black installed, write `pip install black`.
- If there exists formatting and linting errors please type, `python -m black .` to view those errors.

## Example response

![image](https://github.com/acmcsufoss/acmOpportunities/assets/116927138/d4962302-adee-4d41-a2c4-fccdeacd8710)

---

Made with 🐱💙 by [**@boushrabettir**](https://github.com/boushrabettir)
