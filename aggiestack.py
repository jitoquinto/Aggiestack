import argparse
import sys
import json
import os
import socket

def argument_parser():
    #CL Argument Parser
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(help="Commands")

    #config command
    config_parser = subparser.add_parser('config', help="Read Configuration files")
    config_option_group = config_parser.add_mutually_exclusive_group(required=True)
    config_option_group.add_argument('--hardware', action='store',
            help='Specify config file is for hardware.')
    config_option_group.add_argument('--images', action='store',
            help='Specify config file is for images.')
    config_option_group.add_argument('--flavors', action='store',
            help='Specify config file is for flavors.')

    #show command
    show_parser = subparser.add_parser('show', help="Print stored information.")
    show_parser.add_argument('option', action='store', 
            help=""" \t<hardware> Print only hardware information.\n
            \t<images>   Print only available image information.\n
            \t<flavors>  Print information about available flavors.\n
            \t<all>      Print all available information.\n""")

    #admin command
    admin_parser = subparser.add_parser('admin', help="Admin options")
    admin_subparser = admin_parser.add_subparsers(help="Admin functions")
    ##Show subparser
    show_subparser = admin_subparser.add_parser('show', help="Show current available resources")
    show_subparser.add_argument('option', help="\t<hardware>\tShows available resources for each machine.\n\t<instances> Shows where all instances are running.")
    ##can_host subparser
    can_host_parser = admin_subparser.add_parser('can_host', help="Outputs yes if machine has enough resources to host instance")
    can_host_parser.add_argument('machine', action='store',
            help="Name of target host machine")
    can_host_parser.add_argument('flavor', action='store',
            help="Desired Flavor for instance")
    ##evacuate subparser
    evacuate_sub_parser = admin_subparser.add_parser('evacuate', help="Evacuates a Rack")
    evacuate_sub_parser.add_argument('rack_name', action='store', help="The Rack that will be evacuated")
    ##remove subparser
    remove_sub_parser = admin_subparser.add_parser('remove', help='Removes a specified machine from Datacenter.')
    remove_sub_parser.add_argument('machine',action='store',help='The name of the machine that will be removed')
    ##add subparser
    add_sparser = admin_subparser.add_parser('add', help='Add machine to the system')
    add_sparser.add_argument('--mem', action='store',help='The amount of memory the machine has')
    add_sparser.add_argument('--disk', action='store',help='The amount of disks the machine has')
    add_sparser.add_argument('--vcpus',action='store',help='The number of vcpus the machien has')
    add_sparser.add_argument('--ip',action='store',help='The IP of the new machine')
    add_sparser.add_argument('--rack',action='store',help='The rack in which the machine is in')
    add_sparser.add_argument('machine',action='store',help='The name of the machine')

    #server command
    server_parser = subparser.add_parser('server', help="Server Subcommands")
    server_subparser = server_parser.add_subparsers(help="Server Subcommands")
    ##create subparser
    create_subparser = server_subparser.add_parser('create', help="Create a new instance.")
    create_subparser.add_argument('--image', action='store', help='The name of the Image the new instance will be booted from.')
    create_subparser.add_argument('--flavor', action='store', help='The name of the flavor that the instance will be configured as.')
    create_subparser.add_argument('instance_name', action='store',help='Name of the instance to be created')
    ##delete subparser
    delete_subparser = server_subparser.add_parser('delete', help='Delete Instance.')
    delete_subparser.add_argument('instance_name', action='store', help='Name of the instance to be deleted.')
    ##list subparser
    list_subparser = server_subparser.add_parser('list', help='List all running instances.')


    args = vars(parser.parse_args())
    return args

def read_hw(cli_args, fname):
    #reads hw config file and returns a list of dictionaries
    #each dictionary corresponds to an entry in the file.
    full_hdwr = []
    racks = []
    hardware = []
    with open(fname,'r') as confile:
        #reads rack information
        list_size_r = int(confile.readline())
        racks = [dict() for x in range(list_size_r)]
        for i in range(list_size_r):
            r_line = confile.readline()
            r_spec = r_line.strip('\n').split(' ')
            racks[i]['name'] = r_spec[0]
            racks[i]['capacity'] = r_spec[1]
        full_hdwr.append(racks)
        #Original Read Hdwr file
        list_size_h = int(confile.readline())
        hardware = [dict() for x in range(list_size_h)]
        counter = 0
        for line in confile:
            spec_list = line.strip('\n').split(' ')
            hardware[counter]['name'] = spec_list[0]
            hardware[counter]['rack'] = spec_list[1]
            socket.inet_aton(spec_list[2])
            hardware[counter]['ip'] = spec_list[2]
            hardware[counter]['mem'] = int(spec_list[3])
            hardware[counter]['disks'] = int(spec_list[4])
            hardware[counter]['vcpus'] = int(spec_list[5])
            hardware[counter]['a_mem'] = int(spec_list[3])
            hardware[counter]['a_disks'] = int(spec_list[4])
            hardware[counter]['a_vcpus'] = int(spec_list[5])
            counter = counter + 1
    full_hdwr.append(hardware)
    return full_hdwr

def read_img(cli_args, fname):
    #reads images config file and returns a list of dictionaries
    #each dictionary corresponds to an entry in the file.
    images = []
    with open(fname, 'r') as confile:
        list_size = int(confile.readline())
        images = [dict() for x in range(list_size)]
        counter = 0
        for line in confile:
            img_list = line.strip('\n').split(' ')
            images[counter]['name'] = img_list[0]
            images[counter]['size'] = img_list[1] 
            images[counter]['path'] = img_list[2]
            counter = counter + 1
    return images

def read_flav(cli_args, fname):
    #reads flavors config file and returns a list of dictionaries
    #each dictionary corresponds to an entry in the file.
    flavors = []
    with open(fname, 'r') as confile:
        list_size = int(confile.readline())
        flavors = [dict() for x in range(list_size)]
        counter = 0
        for line in confile:
            split_line = line.strip('\n').split(' ')
            flavors[counter]['name'] = split_line[0]
            flavors[counter]['ram'] = int(split_line[1])
            flavors[counter]['disks'] = int(split_line[2])
            flavors[counter]['vcpus'] = int(split_line[3])
            counter = counter + 1
    return flavors

def persist(config):
    #Makes configuration data from file persistent by converting DS to JSON.
    #Since Dictionaries are being used there is no harm in adding identical fields.
    P_File = 'config.json'
    if os.path.isfile(P_File):
        with open(P_File) as json_file:
            data = json.load(json_file)
            for option in config:
                if config[option] is None:
                    continue
                if data[option] is None:
                    data[option] = config[option]
                    continue
                if len(config[option]) == 0:
                    data[option] = None
                    continue
                if len(config[option]) < len(data[option]):
                    data[option] = config[option]
                    continue
                for x in range(len(config[option])):
                    if len(data[option]) < (x+1):
                        data[option].append(config[option][x])
                        continue
                    for key in config[option][x]:
                        data[option][x][key] = config[option][x][key]
            config = data
    json_file = open(P_File,'w+')
    json.dump(config, json_file, indent=2, separators=(',',': '))


def config_option(cli_args):
    #Determines what type of configuration file is given and calls the 
    #appropriate function. Returns the 'config' dictionary which will be
    #added to persisted json file.
    config = {}
    log = open('aggiestack-log.txt','a+')
    for key in cli_args:
        if cli_args[key] is not None:
            if not os.path.isfile(cli_args[key]):
                print "Error: " + cli_args[key] + " does not exist."
                command = ' '.join(sys.argv[1:])
                log.write(command + ' FAILURE\n')
                return
            if key == 'hardware':
                hdwr = read_hw(cli_args,cli_args[key])
                config['racks'] = hdwr[0]
                config['hardware'] = hdwr[1]
                config['images'] = None
                config['flavors'] = None
                config['instances'] = None 
            if key == 'images':
                config['racks'] = None
                config['hardware'] = None
                config['images'] = read_img(cli_args,cli_args[key])
                config['flavors'] = None
                config['instances'] = None
            if key == 'flavors':
                config['racks'] = None
                config['hardware'] = None
                config['images'] = None
                config['flavors'] = read_flav(cli_args, cli_args[key])    
                config['instances'] = None 
    persist(config)


def show_option(cli_args):
    #Print all elements in JSON based on 'option' given
    P_File = 'config.json'
    with open(P_File) as json_file:
        data = json.load(json_file) 
        print '\n*******************************************\n*******************************************\n\t\t' + cli_args['option'].upper() +  '\n*******************************************\n*******************************************'
        if data[cli_args['option']] is None:
            print 'No Configuration Data for ' + cli_args['option'] + ' found.'
            print '\n-------------------------------------------'
            return
        for item in data[cli_args['option']]:
            print 'Name: ' + item['name'] 
            for key in item:
                if key != 'name' and 'a_' not in key and key != 'machine':
                    print key + ":" + str(item[key])
            print '\n-------------------------------------------'

def admin_show(cli_args):
    log = open('aggiestack-log.txt', 'a+')
    P_File = 'config.json'
    if not os.path.isfile(P_File):
        print 'No Configuration Data Found.'
        command = ' '.join(sys.argv[1:])
        log.write(command + ' FAILURE\n')
        return
    with open(P_File) as json_file:
        data = json.load(json_file)
        print '\n*******************************************\n*******************************************\n\t\t' + cli_args['option'].upper() +  '\n*******************************************\n*******************************************'
        if data[cli_args['option']] is None:
            print 'No Data for ' + cli_args['option'] + ' found.'
            print '\n-------------------------------------------'
            return
        for item in data[cli_args['option']]:
            print 'Name: ' + item['name'] 
            if cli_args['option'] == 'hardware':
                for key in item:
                    if key != 'name' and 'a_' in key:
                        print key + ":" + str(item[key])
                print '\n-------------------------------------------'
            else:
                for key in item:
                    if key != 'name':
                        print key + ":" + str(item[key])
                print '\n-------------------------------------------'
    command = ' '.join(sys.argv[1:])
    log.write(command + ' SUCCESS\n')       

        

def can_host(cli_args):
    #finds the given machine and flavor in config file and prints out if flavor can be hosted
    P_File = 'config.json'
    log = open('aggiestack-log.txt', 'a+')
    flavor_mem = 0
    flavor_disk = 0
    flavor_vcpu = 0
    machine_mem = 0
    machine_disk = 0
    machine_vcpu = 0
    if not os.path.isfile(P_File):
        print 'No Configuration Data Found.'
        command = ' '.join(sys.argv[1:])
        log.write(command + ' FAILURE\n')
        return
    with open(P_File) as json_file:
        data = json.load(json_file) 
        for flav in data['flavors']:
            if flav['name'] == cli_args['flavor']:
                flavor_mem = flav['ram']
                flavor_disk = flav['disks']
                flavor_vcpu = flav['vcpus']
        for machine in data['hardware']:
            if machine['name'] == cli_args['machine']:
                machine_mem = machine['a_mem']
                machine_disk = machine['a_disks']
                machine_vcpu = machine['a_vcpus']
        if (machine_mem >= flavor_mem) and (machine_disk >= flavor_disk) and (machine_vcpu >= flavor_vcpu):
            return True
        else:
            return False
    command = ' '.join(sys.argv[1:])
    log.write(command + ' SUCCESS\n')

def create_instance(cli_args,disabled_rack):
    #Create an instance and persist its information. Looks for a machine that can host the instance and modifies its available resources.
    #set default values for flavor and image
    ins_flav = 'small' if cli_args['flavor'] is None else cli_args['flavor']
    ins_image = 'linux-ubuntu' if cli_args['image'] is None else cli_args['image']
    ins_name = cli_args['instance_name']
    ins_machine = {}
    #for persistance
    config = {}
    config['racks'] = None
    config['images'] = None
    config['flavors'] = None
    #load config file 
    log = open('aggiestack-log.txt', 'a+')
    P_File = 'config.json'
    if not os.path.isfile(P_File):
        print 'No Configuration Data Found.'
        command = ' '.join(sys.argv[1:])
        log.write(command + ' FAILURE\n')
        return
    json_file = open(P_File)
    data = json.load(json_file)
    #Look for machine that can host instance
    cli_args['flavor'] = ins_flav
    for machine in data['hardware']:
        cli_args['machine'] = machine['name']
        if can_host(cli_args) and machine['rack'] != disabled_rack:
            ins_machine = machine
            break
    if not ins_machine:
        print 'No machine data found.'
        command = ' '.join(sys.argv[1:])
        log.write(command + ' FAILURE\n')
        return
    #Find information about flavor resources
    flav = {}
    for flavor in data['flavors']:
        if ins_flav == flavor['name']:
            flav = flavor
            break
    if not flav:
        print 'No flavor data found.'
        command = ' '.join(sys.argv[1:])
        log.write(command + ' FAILURE\n')
        return
    #Modify chosen machine to reduce resources
    for machine in data['hardware']:
        if machine is ins_machine:
            machine['a_mem'] = machine['a_mem'] - flav['ram']
            machine['a_vcpus'] = machine['a_vcpus'] - flav['vcpus']
            machine['a_disks'] = machine['a_disks'] - flav['disks']
            break
    config['hardware'] = data['hardware']
    #Create instance object,append, and persist
    ins_instance = {}
    ins_instance['name'] = ins_name
    ins_instance['flavor'] = ins_flav
    ins_instance['image'] = ins_image
    ins_instance['machine'] = ins_machine['name']
    ins_instance['rack'] = ins_machine['rack']
    if data['instances'] is None:
        data['instances'] = []
    data['instances'].append(ins_instance)
    config['instances'] = data['instances']
    persist(config)
    #write to log
    command = ' '.join(sys.argv[1:])
    log.write(command + ' SUCCESS\n')

def delete_instance(cli_args):
    #Looks for instance inside persisted json. Removes instance. Then goes to machine it is located on and modifies resources.
    ins_name = cli_args['instance_name']
    #For persistance
    config = {}
    config['racks'] = None
    config['images'] = None
    config['flavors'] = None
    #load JSON file into data structure
    log = open('aggiestack-log.txt', 'a+')
    P_File = 'config.json'
    if not os.path.isfile(P_File):
        print 'No Configuration Data Found.'
        command = ' '.join(sys.argv[1:])
        log.write(command + ' FAILURE\n')
        return
    json_file = open(P_File)
    data = json.load(json_file)

    #find the instance entry
    inst = {}
    index = 0
    for instance in data['instances']:
        if instance['name'] == ins_name:
            inst = instance
            break
        index = index + 1
    if not inst:
        print 'No instance data found.'
        command = ' '.join(sys.argv[1:])
        log.write(command + ' FAILURE\n')
        return
    #Get Flavor information
    flav = {}
    for flavor in data['flavors']:
        if flavor['name'] == inst['flavor']:
            flav = flavor
            break
    if not flav:
        print 'No flavor data found.'
        command = ' '.join(sys.argv[1:])
        log.write(command + ' FAILURE\n')
        return
    
    #find machine that contains instance and reset resources
    ins_machine = {}
    for machine in data['hardware']:
        if machine['name'] == inst['machine']:
            ins_machine = machine
            machine['a_mem'] = machine['a_mem'] + flav['ram']
            machine['a_vcpus'] = machine['a_vcpus'] + flav['vcpus']
            machine['a_disks'] = machine['a_disks'] + flav['disks']
            break
    if not ins_machine:
        print 'No machine data found.'
        command = ' '.join(sys.argv[1:])
        log.write(command + ' FAILURE\n')
        return   
    #Remove instance from JSON
    del data['instances'][index]
    
    config['instances'] = data['instances']
    config['hardware'] = data['hardware']

    #persist
    persist(config)
    command = ' '.join(sys.argv[1:])
    log.write(command + ' SUCCESS\n')

def add_machine(cli_args):
    #defaults
    mem = 16 if cli_args['mem'] is None else cli_args['mem']
    disk = 16 if cli_args['disk'] is None else cli_args['disk']
    vcpus = 4 if cli_args['vcpus'] is None else cli_args['vcpus']
    ip = "128.0.0.1" if cli_args['ip'] is None else cli_args['ip']
    rack = 'r1' if cli_args['rack'] is None else cli_args['rack']
    name = cli_args['machine']

    #For persistance
    config = {}
    config['racks'] = None
    config['images'] = None
    config['flavors'] = None
    config['instances'] = None
    #load JSON file into data structure
    log = open('aggiestack-log.txt', 'a+')
    P_File = 'config.json'
    if not os.path.isfile(P_File):
        print 'No Configuration Data Found.'
        command = ' '.join(sys.argv[1:])
        log.write(command + ' FAILURE\n')
        return
    json_file = open(P_File)
    data = json.load(json_file)

    #create machine entry
    mac = {}
    mac['name'] = name
    mac['mem'] = mem
    mac['ip'] = ip
    mac['disks'] = disk
    mac['vcpus'] = vcpus
    mac['rack'] = rack
    mac['a_mem'] = mem
    mac['a_vcpus'] = vcpus
    mac['a_disks'] = disk
    #Add machine to JSON
    if len(data['hardware']) == 0:
        data['hardware'] = []
    data['hardware'].append(mac)
    #Persist
    config['hardware'] = data['hardware']
    persist(config)
    command = ' '.join(sys.argv[1:])
    log.write(command + ' SUCCESS\n')

def remove_machine(cli_args):
    name = cli_args['machine']

    #For persistance
    config = {}
    config['racks'] = None
    config['images'] = None
    config['flavors'] = None
    config['instances'] = None
    #load JSON file into data structure
    log = open('aggiestack-log.txt', 'a+')
    P_File = 'config.json'
    if not os.path.isfile(P_File):
        print 'No Configuration Data Found.'
        command = ' '.join(sys.argv[1:])
        log.write(command + ' FAILURE\n')
        return
    json_file = open(P_File)
    data = json.load(json_file)

    #remove machine from datacenter
    machine = {}
    index = 0
    for m in data['hardware']:
        if m['name'] == name:
            machine = m
            break
        index = index + 1
    if not machine:
        print 'No machine data found.'
        command = ' '.join(sys.argv[1:])
        log.write(command + ' FAILURE\n')
        return 
    del data['hardware'][index]
    config['hardware'] = data['hardware']
    persist(config)

    #look for affected instances and transfer to a new machine
    instances = []
    if data['instances'] is not None:
        for inst in data['instances']:
            if inst['machine'] == name:
                instances.append(inst)
                cli_args['instance_name'] = inst['name']
                delete_instance(cli_args)
        for inst in instances:
            cli_args['image'] = inst['image']
            cli_args['flavor'] = inst['flavor']
            cli_args['instance_name'] = inst['name']
            create_instance(cli_args,'N/A')
    command = ' '.join(sys.argv[1:])
    log.write(command + ' SUCCESS\n')

def evacuate_rack(cli_args):
    rack_name = cli_args['rack_name']

    #load JSON file into data structure
    log = open('aggiestack-log.txt', 'a+')
    P_File = 'config.json'
    if not os.path.isfile(P_File):
        print 'No Configuration Data Found.'
        command = ' '.join(sys.argv[1:])
        log.write(command + ' FAILURE\n')
        return
    json_file = open(P_File)
    data = json.load(json_file)

    #get other available racks
    racks = []
    for rack in data['racks']:
        if rack['name'] != rack_name:
            racks.append(rack)
    if len(racks) == 0:
        print 'ERROR: No other available racks to evacuate to.'
        command = ' '.join(sys.argv[1:])
        log.write(command + ' FAILURE\n')
        return
    #look for affected instances and transfer to a new machine
    instances = []
    if data['instances'] is not None:
        for inst in data['instances']:
            if inst['rack'] == rack_name:
                instances.append(inst)
                cli_args['instance_name'] = inst['name']
                delete_instance(cli_args)
        for inst in instances:
            cli_args['image'] = inst['image']
            cli_args['flavor'] = inst['flavor']
            cli_args['instance_name'] = inst['name']
            create_instance(cli_args,rack_name) 
    command = ' '.join(sys.argv[1:])
    log.write(command + ' SUCCESS\n')
def main():
    cli_args = argument_parser()
    show_all_opt = ['hardware','images','flavors','racks']
    log = open('aggiestack-log.txt', 'a+')
    if sys.argv[1] == 'config':
        try:
            config_option(cli_args)
            command = ' '.join(sys.argv[1:])
            log.write(command + ' SUCCESS\n')
        except Exception, e:
            print "Error: " + str(e)
            command = ' '.join(sys.argv[1:])
            log.write(command + ' FAILURE\n')
            
    elif sys.argv[1] == 'show':
        P_File = 'config.json'
        log = open('aggiestack-log.txt', 'a+')
        if not os.path.isfile(P_File):
            print 'No Configuration Data Found.'
            command = ' '.join(sys.argv[1:])
            log.write(command + ' FAILURE\n')
            return
        if cli_args['option'] == 'all':
            for item in show_all_opt:
                cli_args['option'] = item
                show_option(cli_args)
        else:
            show_option(cli_args)
        command = ' '.join(sys.argv[1:])
        log.write(command + ' SUCCESS\n')
    elif sys.argv[1] == 'admin':
        if sys.argv[2] == 'can_host':
            can_host(cli_args)
        elif sys.argv[2] == 'show':
            admin_show(cli_args)
        elif sys.argv[2] == 'add':
            add_machine(cli_args)
        elif sys.argv[2] == 'evacuate':
            evacuate_rack(cli_args)
        elif sys.argv[2] == 'remove':
            remove_machine(cli_args)
            
    elif sys.argv[1] == 'server':
        if sys.argv[2] == 'list':
            cli_args['option'] = 'instances'
            show_option(cli_args)
            command = ' '.join(sys.argv[1:])
            log.write(command + ' SUCCESS\n')
        elif sys.argv[2] == 'delete':
            delete_instance(cli_args)
        elif sys.argv[2] == 'create':
            create_instance(cli_args,'N/A')
        

if __name__ == "__main__":
    main()