cd /*path to folder */
/usr/bin/python3.10 -m gunicorn src.main:app --workers 24 --worker-class uvicorn.workers.UvicornWorker --bind localhost:/*port*/