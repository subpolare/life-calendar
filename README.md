<div align="center">
  <h1>Calendar of Life </h1>
</div>

Welcome to the [Calendar of Life](https://t.me/TimeGridBot) codebase. We're building our own life expand community. We've opensourced the code so that everyone can learn about how collections are created and the community is regulated. We also leave the opportunity for participants to modify the code and propose those changes that they consider necessary.

We only use articles from the [nature jornals](https://www.nature.com/siteindex) (preferring only nature and nature review journals) as a source of information for newsletters. We try to keep the database of articles and journals extremely limited and manually reviewed by our specialists. This is how we try to be as scientifically correct as possible. 

## 🔮 Tech stack with sleek badge showcase

⚙️ TL;DR: Python, JavaScript, Postgres, telegram bots

We try to keep our code simple and stupid, because we are not very smart ourselves, and the only developer is a bioinformatician. We used Python almost everywhere, but JavaScript was used to generate the calendar but in the future we want to rewrite [encryption](https://github.com/subpolare/life-calendar/blob/main/security/encryption.py) in Go (for educational purposes). The database is built in PostgreSQL.

![python](https://img.shields.io/badge/python%20-%2314354C.svg?&style=for-the-badge&logo=python&logoColor=white) ![asyncio](https://img.shields.io/badge/asyncio-%2300BAFF.svg?&style=for-the-badge&logo=python&logoColor=white) ![docker](https://img.shields.io/badge/docker-%232496ED.svg?&style=for-the-badge&logo=docker&logoColor=white) ![postgres](https://img.shields.io/badge/postgres-%23316192.svg?&style=for-the-badge&logo=postgresql&logoColor=white) ![javascript](https://img.shields.io/badge/javascript%20-%23323330.svg?&style=for-the-badge&logo=javascript&logoColor=%23F7DF1E) ![github](https://img.shields.io/badge/github%20actions%20-%232671E5.svg?&style=for-the-badge&logo=github%20actions&logoColor=white) ![git](https://img.shields.io/badge/git%20-%23F05033.svg?&style=for-the-badge&logo=git&logoColor=white)

If you want to install and run our project locally, copy this repository and create a `.env` file with the required variables. 

```bash
git clone https://github.com/subpolare/life-calendar.git
cd life-calendar
```

Make sure that [Docker](https://www.docker.com/get-started) is installed and run the following step (if you don't want to see the logs, run with `-d`): 

```bash
docker compose up --build
```

## 👩‍💼 MIT License 

[MIT](LICENSE.md) — you can use the code for private and commercial purposes with an author attribution (by including the original license file or mentioning us). Feel free to contact us via email [nachatoi@list.ru](mailto:nachatoi@list.ru).

