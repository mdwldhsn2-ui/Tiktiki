# ১. পাইথন ৩.৯ ভার্সন দিয়ে শুরু করা
FROM python:3.9

# ২. সার্ভারের এনভায়রনমেন্ট আপডেট করা
RUN apt-get update && apt-get install -y wget gnupg2 unzip

# ৩. গুগল ক্রোম ব্রাউজার ডাউনলোড এবং ইনস্টল করা
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# ৪. প্রোজেক্টের ফোল্ডার সেটআপ করা
WORKDIR /app

# ৫. আপনার ফোল্ডারের সব ফাইল সার্ভারে কপি করা
COPY . /app

# ৬. requirements.txt থেকে সব লাইব্রেরি ইনস্টল করা
RUN pip install --no-cache-dir -r requirements.txt

# ৭. সবশেষে আপনার বট রান করা
CMD ["python", "bot.py"]