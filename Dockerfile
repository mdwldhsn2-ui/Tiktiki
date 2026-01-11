# ১. পাইথন ৩.৯ ভার্সন
FROM python:3.9

# ২. প্রাথমিক টুলস ইনস্টল করা (gnupg এখানে জরুরি)
RUN apt-get update && apt-get install -y wget gnupg2 unzip curl

# ৩. Google Chrome-এর কি (Key) আধুনিক পদ্ধতিতে সেটআপ করা (apt-key ছাড়া)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /usr/share/keyrings/google-chrome.gpg \
    && echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main' > /etc/apt/sources.list.d/google-chrome.list

# ৪. এবার ক্রোম ব্রাউজার ইনস্টল করা
RUN apt-get update && apt-get install -y google-chrome-stable

# ৫. ডিসপ্লে পোর্ট সেট করা
ENV DISPLAY=:99

# ৬. প্রোজেক্ট ফাইল কপি করা
WORKDIR /app
COPY . /app

# ৭. লাইব্রেরি ইনস্টল করা
RUN pip install --no-cache-dir -r requirements.txt

# ৮. বট রান করা
CMD ["python", "bot.py"]
