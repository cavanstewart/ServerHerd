import asyncio
import sys
import time
import aiohttp
import json
import async_timeout
import re
#ports 12696-12704       

api_key = "AIzaSyBQMYOM_KtUsb1nvSWlMZV0l9223uWetw8"
palces_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?"

client_dict = {}
talks_dict = {
 'Goloman': ['Hands', 'Holiday', 'Wilkes'], 
 'Hands': ['Goloman', 'Wilkes'],
 'Holiday': ['Goloman', 'Welsh', 'Wilkes'],
 'Welsh': ['Holiday'],
 'Wilkes': ['Hands', 'Goloman', 'Holiday']
}
port_dict = {
 'Goloman': 12696,
 'Hands': 12697,
 'Holiday': 12698,
 'Welsh': 12699,
 'Wilkes': 12700
}

tasks = {}

async def flood(client_name):
 server_name = sys.argv[1]
 for talks_with in talks_dict[server_name]:
  log_file.write("Attempting to open connection with server {0} at port {1}...".format(talks_with, port_dict[talks_with]))
  try:
   
   reader, writer = await asyncio.open_connection('127.0.0.1', port_dict[talks_with], loop=loop)
   log_file.write("Success\n")
   message = client_dict[client_name]
   #print(message)
   
   log_file.write("SENDING: " + message)
   writer.write(message.encode())
   await writer.drain()
   writer.close()
  except:
   log_file.write("Fail\n")
   pass
   

def getLatLon(location):
 loc_list = re.split(r"([-|+])", location)
 lat = ''
 lon = ''
 if loc_list[1] == "+":
  lat = loc_list[2]
 else:
  lat = loc_list[1] + loc_list[2]
 if loc_list[3] == "+":
  lon = loc_list[3]
 else:
  lon = loc_list[3] + loc_list[4]
 return [lat, lon]


def main():
 if(len(sys.argv) != 2):
  raise Exception("too many arguements Usage: python3 server.py [servername]")
 server_name = sys.argv[1]
 port = port_dict[server_name]

 global log_file
 log_file = open(server_name + "_log.txt", "w+")

 global loop
 loop = asyncio.get_event_loop()
 conn = asyncio.start_server(handle_connection, host='127.0.0.1', port=port, loop=loop)
 server = loop.run_until_complete(conn)
 try:
  loop.run_forever()
 except KeyboardInterupt:
  pass
 finally:
  server.close()
  loop.run_until_complete(server.wait_closed())
  loop.close()
  log_file.close()


async def respond(message):
 message_list = message.split()
 current_time = time.time()
 name = sys.argv[1]
 return_message = ""
 #handle IAMAT
 if message_list[0] == "IAMAT":
  client_time = float(message_list[3])
  diff_time = current_time - client_time
  diff_time_str = str(diff_time)
  
  if diff_time >= 0:
   diff_time_str = "+" + diff_time_str
  else:
   diff_time_str = "-" + diff_time_str

  client_name = message_list[1]
  
  return_message = "AT " + name + " " + diff_time_str + " " +  client_name + " " + message_list[2] + " " + message_list[3] + "\n"
  client_dict[client_name] = return_message
  asyncio.ensure_future(flood(client_name))

 #handle WHATSAT
 if message_list[0] == "WHATSAT":
  
  client_name = message_list[1]
  if client_name not in client_dict:
   return_message = "? " + message
  else:
   return_message = client_dict[client_name]
   return_list = return_message.split()
   loc_list = getLatLon(return_list[4])
   lat = loc_list[0]
   lon = loc_list[1]
   radius = message_list[3]
   url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=%s,%s&radius=%d&key=%s' % (lat, lon, float(radius), api_key)

   #print(url)

   async with aiohttp.ClientSession() as session:
    google_json = ""
    async with async_timeout.timeout(10):
     async with session.get(url) as response:
      google_json = await response.json()
    
    num_results = message_list[2]
    #print(google_json)
    results = google_json['results'][:int(num_results)]
    #print(json.dumps(results, indent=3))
    return_message =  return_message + "\n" + json.dumps(results, indent=3) + "\n"
   
 return return_message


async def handle_connection(reader, writer):
 
 data = await reader.readline()
 message = data.decode()
 log_file.write("RECEIVED: " + message)
 
 message_list = message.split()

 #return_message = ""

 #Handle AT (flooding)
 if message_list[0] == "AT":
  #print("recieved AT")
  client_name = message_list[3]
  if client_name in client_dict:
   if message == client_dict[client_name]:
    #print("Recieved redundant info\n")
   else:
    client_dict[client_name] = message
    asyncio.ensure_future(flood(client_name))
  else:
   client_dict[client_name] = message
   asyncio.ensure_future(flood(client_name))
 elif message_list[0] == "IAMAT" or message_list[0] == "WHATSAT":
  send_it = await respond(message)
  log_file.write("SENDING: " + send_it)
  writer.write(send_it.encode())
  await writer.drain()
  writer.close()
 else:
  send_it = "? " + message
  log_file.write("SENDING: " + send_it)
  writer.write(send_it.encode())
  await writer.drain()
  writer.close()
  



if __name__ == '__main__':
 main()
