#!/usr/bin/env python2.6
# encoding: utf8

import grp
import os
import pwd
import socket
import subprocess
import sys

def main():
    
    VPS_HOSTNAME = 's15323772.onlinehome-server.com'

    # Get the path of the www root.
    if len(sys.argv) >= 2:
        www_root = os.path.abspath(sys.argv[1])
    else:
        print 'WARNING: Path to www_root not specified!'
        print
        www_root = os.getcwd()

    # Make sure that httpdocs exists.
    httpdocs = www_root + '/httpdocs'
    if not os.path.exists(httpdocs):
        print 'ERROR: %r does not exist!' % httpdocs
        exit(1)

    # Determine if this is the VPS or not.
    hostname = socket.gethostname()
    is_vps = hostname == VPS_HOSTNAME

    print 'hostname: %s' % hostname
    print 'www_root: %s' % www_root
    print
    if is_vps:
        print 'This is the vps.'
    else:
        print 'This IS NOT the vps! (%s)' % VPS_HOSTNAME
    print

    # Some basic checking to make sure the www root is in the right place.
    if is_vps and not www_root.startswith('/var/www/vhosts/'):
        print 'ERROR: www_root should be under %r.' % '/var/www/vhosts'
        exit(1)


    # Defaults for usernames and groups.
    user = None
    user_id = -1
    group = None
    group_id = -1
    psaserv_id = -1
    root_id = 0


    # Parse out the user/group name/id that CGIs need to run under on the server.
    if is_vps:
        conf = '/'.join(www_root.split('/')[:5]) + '/conf/httpd.include'
        for line in open(conf, 'rb'):
            line = line.strip().split()
            if len(line) == 3 and line[0] == 'SuexecUserGroup':
                _, user, group = line
                break
        else:
            print 'ERROR: We did not find %r in the config file!' % 'SuexecUserGroup'
            exit(1)
    
        user_id = pwd.getpwnam(user).pw_uid
        group_id = grp.getgrnam(group).gr_gid
        psaserv_id = grp.getgrnam('psaserv').gr_gid
    
        print 'suexec user : %r (%d)' % (user, user_id)
        print 'suexec group: %r (%d)' % (group, group_id)
        print 'server group: %r (%d)' % ('psaserv', psaserv_id)
        print


    # Build up the perms/uid/gid for all the paths that the VPS requires.
    vps_specifics = (
    	(0750, user_id, psaserv_id, 'anon_ftp'),
    	(0755, root_id, psaserv_id, 'bin'),
    	(0750, user_id, psaserv_id, 'cgi-bin'),
    	(0750, root_id, psaserv_id, 'conf'),
    	(0755, root_id, psaserv_id, 'error_docs'),
    	(0750, user_id, psaserv_id, 'httpdocs'),
    	(0750, user_id, psaserv_id, 'httpsdocs'),
    	(0750, root_id, psaserv_id, 'pd'),
    	(0700, user_id, root_id   , 'private'),
    	(0550, root_id, psaserv_id, 'statistics'),
    	(0755, root_id, psaserv_id, 'subdomains'),
    	(0755, root_id, psaserv_id, 'web_users'),
    )
    non_vps_perms = 0777 # For the above files when not on the vps.
    httpdocs_dir  = 0755 if is_vps else 0777
    httpdocs_file = 0644 if is_vps else 0666
    httpdocs_cgi  = 0750 if is_vps else 0777


    def set_meta(path, perms=None, uid=None, gid=None):
        if not os.path.exists(path):
            return None
        actions = []
        stat = os.stat(path)
        if perms is not None and stat.st_mode & 0o777 != perms:
            actions.append('perms=%o' % perms)
            os.chmod(path, perms)
        if uid is not None and uid > -1 and stat.st_uid != uid:
            actions.append('owner=%s' % uid)
            os.chown(path, uid, -1)
        if gid is not None and gid > -1 and stat.st_gid != gid:
            actions.append('group=%s' % gid)
            os.chown(path, -1, gid)
        return actions

    print 'Setting meta of Plesk directories...'
    for perms, uid, gid, filename in vps_specifics:
        path = www_root + '/' + filename
        if is_vps:
            actions = set_meta(path, perms, uid, gid)
        else:
            actions = set_meta(path, non_vps_perms)
        if actions:
            print '\t%s (%s)' % (path, ', '.join(actions))
    
    print 'Setting meta of httpdocs contents...'
    for dirpath, dirnames, filenames in os.walk(httpdocs):
        for name in filenames + dirnames:
            path = dirpath + '/' + name
            if os.path.isdir(path):
                perms = httpdocs_dir
            elif os.path.splitext(path)[1].endswith('cgi'):
                perms = httpdocs_cgi
            else:
                perms = httpdocs_file
            actions = set_meta(path, perms, user_id, group_id)
            if actions:
                print '\t%s (%s)' % (path, ', '.join(actions))

    print 'Done.'


if __name__ == '__main__':
    main()