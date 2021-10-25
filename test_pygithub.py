# https://medium.com/geekculture/files-on-heroku-cd09509ed285
#
from github import Github

token = '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'
g = Github(token)

github = Github('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')

repository = g.get_user().get_repo('heroku3')
# path in the repository
filename = 'files/file.json'
content = '{\"name\":\"beppe\",\"city\":\"amsterdam\"}'
# create with commit message
f = repository.create_file(filename, "create_file via PyGithub", content)


# using an access token


# Github Enterprise with custom hostname
# g = Github(base_url="https://{hostname}/api/v3", login_or_token="access_token")

# Then play with your Github objects:
for repo in g.get_user().get_repos():
    print(repo.name)


# github = Github('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')
# repository = github.get_user().get_repo('my_repo')
# # path in the repository
# filename = 'files/file.json'
# file = repository.get_contents(filename)
# print(file.decoded_content.decode())