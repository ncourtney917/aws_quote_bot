import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import random
import os
import csv
import json
import boto3
from io import StringIO  

def lambda_handler(event,context):
    s3 = boto3.client('s3')
    bucket_name = 'dailyinspiration5520'
    
    # Read in quote list
    quote_list = 'daily_quotes.csv'
    csvfile = s3.get_object(Bucket=bucket_name, Key=quote_list)
    csvlines = csvfile['Body'].read().decode('utf-8-sig').splitlines(True)
    reader = csv.DictReader(csvlines)

    # Randomly pick a quote number
    quote_number = random.choice(range(len(csvlines)-1))
    
    # Pick out the quote that matches the number. Recreate the CSV but with this quote removed
    header = ['Author','Quote','Source','Date']
    body = StringIO() #because s3 require bytes or file like obj
    writer = csv.DictWriter(body, fieldnames=header)
    writer.writeheader()
    for i, row in enumerate(reader):
        if i == quote_number:
            today_quote = row
        else:
            writer.writerow(row)
    
    # Output the CSV without today's quote
    csvS3 = body.getvalue()
    s3.put_object(Body=csvS3, Bucket=bucket_name, Key=quote_list)
    
    # Get quote contents
    author = today_quote['Author']
    quote = today_quote['Quote']
    source = today_quote['Source']
    
    # Get today's date
    today = datetime.today().date()
    today_date = datetime.strftime(today, '%m/%d/%Y')
    print(author, quote, source, today_date)
    
    ############### Log quote
    
    logpath = 'log_file.csv'
    header = ['Date','Author','Quote']
    log_entry = {'Date':today_date,'Author':author,'Quote':quote}
    body = StringIO() #because s3 require bytes or file like obj
    writer = csv.DictWriter(body, fieldnames=header)
    writer.writeheader()
    try:
        logfile = s3.get_object(Bucket=bucket_name, Key=logpath)
        loglines = logfile['Body'].read().decode('utf-8-sig').splitlines(True)
        logreader = csv.DictReader(loglines)
        for item in logreader:
            print(item)
            writer.writerow(item)
    except Exception as e:
        print('file did not exist')
    writer.writerow(log_entry)        
    csvS3 = body.getvalue()
    s3.put_object(Body=csvS3, Bucket=bucket_name, Key=logpath)
    
    
    # Email configuration
    sender_email = "dailyinspiration5520@gmail.com"
    receiver_email = "kgallic@gmail.com"
    cc_email = "nickcourtney22@gmail.com"
    password = 'Natrina812!'
    
    message = MIMEMultipart("alternative")
    message["Subject"] = f"Daily Inspiration from Nick - {today_date}"
    message["From"] = sender_email
    message["To"] = receiver_email
    message['Cc'] = cc_email
    recipients = list([receiver_email,cc_email])
    print(recipients)
    
    greetings = ['Good evening Katrina,',"What's up, KG?","Hope you're having a fantastic day!","Howdy","Hi there. It's me.","Another day, another quote.","Hola"]
    greeting = random.choice(greetings)
    
    # Create the plain-text and HTML version of your message
    html = f"""\
    <html>
      <body>
        <p>{greeting}<br><br>
           Here's your daily bit of inspiration for the day:<br><br>
           <i>"{quote}"</i><br>
           -{author}, <i>{source}</i><br><br>
           Love,<br>
           Nick
        </p>
      </body>
    </html>
    """
    
    # Turn these into plain/html MIMEText objects
    #part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    
    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    #message.attach(part1)
    message.attach(part2)
    print('here')
    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, recipients, message.as_string()
        )
        
    
    if i < 10:
                # Create the plain-text and HTML version of your message
        html = f"""\
        <html>
          <body>
            <p>There are only {i} quotes remaining in the dailyinspiration5520 bucket. Add some new ones!
            </p>
          </body>
        </html>
        """
        
        # Turn these into plain/html MIMEText objects
        #part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        
        # Add HTML/plain-text parts to MIMEMultipart message
        # The email client will try to render the last part first
        #message.attach(part1)
        message = MIMEMultipart("alternative")
        message["Subject"] = f"New Quotes Needed"
        message["From"] = sender_email
        message["To"] = cc_email
        message.attach(part2)
        # Create secure connection with server and send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(
                sender_email, cc_email, message.as_string()
            )
    
    return {
        'statusCode': 200,
        'body': json.dumps(f'{quote}')
    }
