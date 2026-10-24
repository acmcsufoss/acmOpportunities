# [❗UNDER CONSTRUCTION❗] acmOpportunities

The acmOpportunities Discord Bot is a tool designed for students in our club.
This bot keeps developers informed about the latest job opportunities in the
industry by sending job listings directly to the ACM Discord server.

## Key features

- **Stay informed**: Filtered by AI, acmOpportunities keeps up-to-date with the
  latest SWE job opportunities near Fullerton, CA without having to manually
  search for them.
- **Seamless integration**: With the integration of PostgreSQL and Discord,
  acmOpportunities provides a seamless user experience.

## Usage

1. Install [Python](https://www.python.org/downloads/) and
   [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Install dependencies using `uv sync`.

3. Set the required environment variables located in `.env.example`.
4. To create the table, write `uv run python ./main.py --create` once.
5. To run the program manually, write `uv run python ./main.py --days-needed 2`.

> ℹ️ **PLEASE NOTE THE FOLLOWING** ℹ️<br/> Please adjust the amount of days
> needed when using the `--days-needed` command.<br/> **Additionally**, please
> update the workflow in `./github/workflows` to correspond to the wanted amount
> of days.

## Develop

- To check formatting, run `uv run black .`.

## Example response

![image](https://github.com/acmcsufoss/acmOpportunities/assets/116927138/d4962302-adee-4d41-a2c4-fccdeacd8710)

---

Made with 🐱💙 by [**@boushrabettir**](https://github.com/boushrabettir)
