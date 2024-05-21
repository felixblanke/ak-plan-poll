# Conference preference polling

Simple flask app to poll the preferences of conference participants for different workshops.
The collected preferences are used as an input to [optimize the conference schedule](https://github.com/Die-KoMa/ak-plan-optimierung).

### Setup
Simply install [flask](https://flask.palletsprojects.com) and [deploy the app on your webserver](https://flask.palletsprojects.com/en/3.0.x/deploying/).

The directory where the conference configuration files are read from is determined by the config flag `DATA_DIR`, defaulting to `data`.
The export directory is set via `EXPORT_DIR` with default value `export`.
To change these values simply create a `config.json` file in the cloned git repo:
```json
{
    "DATA_DIR": "NEW_DATA_DIR_PATH",
    "EXPORT_DIR": "NEW_EXPORT_DIR_PATH"
}
```

### Configuration

To configure a conference, create a json file at `DATA_DIR/<poll_name>.json`.
Your poll will then be available at `your-conference.example.com/<poll_name>`.
The expected contents of the file follow the [input specification of the scheduling optimizer](https://github.com/Die-KoMa/ak-plan-optimierung/wiki/Input-&-output-format#input--output-format), although only a subset of the content is required.
To create your configuration, you can follow this minimal example:
```json
{
  "timeslots": {
    "info": {
      "blocknames": [
        ["Friday", "afternoon"],
        ["Friday", "evening"],
        ["Saturday", "afternoon"],
        ["Sunday", "morning"]
      ]
    }
  },
  "aks": [
    {
      "info": {
        "name": "WORKSHOP1_NAME",
        "description": "WORKSHOP1_DESCRIPTION",
        "head": "WORKSHOP1_LEADER",
        "reso": false
      }
    }
  ],
  "info": {
    "title": "CONFERENCE_TITLE",
    "block_info_html": "optional HTML code to be included before the time constraints section",
    "ak_info_html": "optional HTML code to be included before the workshop preference section"
  }
}
```

### Export

The response of each participant will be stored at `EXPORT_DIR/<poll_name>/<uuid>.json` where `<uuid>` is a generated UUID1.

An ad hoc evaluation of all responses so far can be accessed at `your-conference.example.com/result/<poll_name>`.
