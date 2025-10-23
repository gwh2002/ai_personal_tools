#!/bin/bash

# To list the URLs of all your Cloud Run services:
gcloud run services list \
  --platform managed \
  --region us-central1 \
  --project assembled-wh

# # To get just one service’s URL:
gcloud run services describe service-name \
  --platform managed \
  --region us-central1 \
  --format "value(status.url)"