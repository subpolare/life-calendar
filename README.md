# Calendar of Life 

Welcome to the [Calendar of Life](https://t.me/TimeGridBot) codebase. We're building our own life expand community. We've opensourced the code so that everyone can learn about how collections are created and the community is regulated. We also leave the opportunity for participants to modify the code and propose those changes that they consider necessary.

We only use articles from the [nature jornals](https://www.nature.com/siteindex) (preferring only nature and nature review journals) as a source of information for newsletters. We try to keep the database of articles and journals extremely limited and manually reviewed by our specialists. This is how we try to be as scientifically correct as possible. 

## 🛠 Tech stack

We try to keep our code simple and stupid, because we are not very smart ourselves, and the only developer is a bioinformatician. We only used Python and PostgreSQL but in the future we want to move calendar generation to JavaScript and encryption to Go.

![python](https://img.shields.io/badge/python%20-%2314354C.svg?&style=for-the-badge&logo=python&logoColor=white) ![asyncio](https://img.shields.io/badge/asyncio-%2300BAFF.svg?&style=for-the-badge&logo=python&logoColor=white) ![docker](https://img.shields.io/badge/docker-%232496ED.svg?&style=for-the-badge&logo=docker&logoColor=white) ![postgres](https://img.shields.io/badge/postgres-%23316192.svg?&style=for-the-badge&logo=postgresql&logoColor=white) ![git](https://img.shields.io/badge/git%20-%23F05033.svg?&style=for-the-badge&logo=git&logoColor=white) 

## 🔮 Installing and running locally

Make sure Docker and docker-compose are installed. Create a `.env` file with the required variables and run:

```bash
docker-compose build
docker-compose up -d
```

## 👩‍💼 License 

[MIT](LICENSE.md) — you can use the code for private and commercial purposes with an author attribution (by including the original license file or mentioning us). Feel free to contact us via email [nachatoi@list.ru](mailto:nachatoi@list.ru).

