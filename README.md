Setup the Sonarqube and it's corresponding database with the compose file `./sonarqube-compose.yml`:
```bash
docker compose -f sonarqube-compose.yml up
```

When those are started you can login the dashboard at `http://localhost:9000/` (Original credentials is admin and admin, then change your password)
Then you need to go into top right corner of your profile --> My Account --> Security
Then generate a token (Global Analysis Token) and save the TOKEN generated to be used for the scanner.

Then you can run the scanner with this image:
```bash
docker run --rm \
  --network home-assistant-core-ht25_sonarnet \
  -v <PROJECT_DIR>:/usr/src \
  -e SONAR_HOST_URL=http://sonarqube:9000 \
  -e SONAR_TOKEN=<SONAR_TOKEN> \
  sonarsource/sonar-scanner-cli
```

And change the project directory to the location of the directory, and also change the sonar token to what
you generated in the dashboard.

The scanner can run for about ~7 minutes and when it's done it will automatically remove itself and post a link in the terminal
like this: `ANALYSIS SUCCESSFUL, you can find the results at: http://sonarqube:9000/dashboard?id=home-assistant-core-ht25`, which you
can access if you swap the `sonarqube` with `localhost`. If you don't see that its done yet, just wait for some time.
