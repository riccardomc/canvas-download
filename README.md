# Download Canvas Files

I want to download all files from a course referenced in the syllabus and each page.
This is a crude way to do just that.

```
pip install -r requirements.txt
export CANVAS_API_KEY="your canvas token"
python3 ./download.py https://canvas.uva.nl/courses/19128/
```

This is very specific to my usecase, so it might not work for many institutions.
