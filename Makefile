extract:
	pybabel extract --input-dirs=. -o locales/messages.pot

init:
	pybabel init -i locales/messages.pot -d locales -D messages -l en
	pybabel init -i locales/messages.pot -d locales -D messages -l uz
compile:
	pybabel compile -d locales -D messages
update:
	pybabel update -d locales -D messages -i locales/messages.pot




git init
git add *
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/aziz-dev23/imtihon_5.git
git push -u origin main