Branches and flow summary:

dev - the development branch
prod - the production branch
ubuntu - deployment on ubuntu 22.04 LTS (ghormley.net)

Generally changes should flow from dev to prod to deployment branches:

git co prod
git merge dev

dev
 +--prod
     +--ubuntu

Never merge ubuntu back to dev or prod.

IMPORTANT:
When setting up remotes on the same server hosting the repository, use the ssh: scheme, not a file scheme. This prevents file creation/permission issues.
