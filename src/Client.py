import threading
import Leecher
import Seeder


def main():
    usr = input("Are you a Seeder (Y/N):\n")
    if(usr == 'N'):
        user_input_event = threading.Event()
        leecher_thread = threading.Thread(target=Leecher.run_leecher, args=(user_input_event,))
        leecher_thread.start()
        user_input_event.wait()
        seeder_thread = threading.Thread(target=Seeder.start_seeder)
        seeder_thread.start()
    else:
        leecher_thread = threading.Thread(target=Leecher.run_leecher)
        seeder_thread = threading.Thread(target=Seeder.start_seeder)
        seeder_thread.start()
        leecher_thread.start()

    

main()