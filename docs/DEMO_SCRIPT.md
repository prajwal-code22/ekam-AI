# 90-second demo script

Target: 80 seconds, under 15 MB, you on camera for the first 10+ seconds.

| Time | Show | Say |
|---|---|---|
| 0:00-0:12 | You on camera | "Hi, I'm Prajwal Siwakoti, a software engineer from Kathmandu, Nepal. This is E-Kaam AI." |
| 0:12-0:25 | You on camera or a simple slide | "In Nepal, many people who need a plumber or electrician, and many workers looking for jobs, are not comfortable with forms or English apps. So finding work is slow and unfair." |
| 0:25-0:55 | Screen recording on phone or browser | Tap the mic, say a real request in Nepali. "I just speak. Gemini understands Nepali, picks the trade, urgency and a fair price, and my GPS location is used automatically." Show the job card. |
| 0:55-1:10 | Worker list | "It then shows the nearest available workers, and I can call one straight away." |
| 1:10-1:20 | You on camera | "E-Kaam AI helps households and daily-wage workers in Nepal connect in their own language. Built with Gemini API and Cloud Run. Thank you." |

Compress to 720p and under 15 MB:

```bash
ffmpeg -i demo.mp4 -vf scale=-2:720 -r 24 -crf 30 -c:a aac -b:a 64k demo_small.mp4
```

Open the Drive link in an incognito window to confirm "Anyone with the link" works.
