# Build and deploy

Command to build the application. 
```
gcloud builds submit --tag gcr.io/shivani-pal-fall2023/streamlit-shivani  --project=shivani-pal-fall2023
```

Command to deploy the application
```
gcloud run deploy --image gcr.io/shivani-pal-fall2023/streamlit-shivani --platform managed  --project=shivani-pal-fall2023 --allow-unauthenticated
```
