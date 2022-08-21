#! /usr/bin/env python3
# coding: utf-8
#
# Copyright 2017 Aaron Bulmahn (aarbudev@gmail.com)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Intel Corporation nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

loginUrl="http://{0}/rpc/WEBSES/create.asp"
jnlpUrl = "http://{0}/Java/jviewer.jnlp?EXTRNIP={0}&JNLPSTR=JViewer"
jarBase = "http://{0}/Java/release/"
mainClass = "com.ami.kvm.jviewer.JViewer"

from urllib.request import urlopen, urlretrieve, Request
from urllib.parse import urlencode
from urllib.error import HTTPError
from http.client import IncompleteRead

import argparse, sys, os, re, subprocess, platform, getpass, zipfile

def usage(argparser):
    argparser.print_help()
    sys.exit(1)

def find_property(settings, property):
    if re.search("%s\s*=(.*)\n" % property, settings):
        return re.search("%s\s*=(.*)\n" % property, settings).group(1).strip()
    return ""

def find_java(argparser):
    java = "java"
    if os.getenv('JVIEWER_JAVA_HOME'):
        java = "%s/bin/java" % os.environ.get('JVIEWER_JAVA_HOME')
        print("Using java: %s" % java)

    try:
        cmd = "%s -XshowSettings -version" % java
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print("Error: %s" % e.stdout.decode('UTF-8'))
        usage(argparser)

    settings = result.stdout.decode('UTF-8')
    version = find_property(settings, 'java.version')
    arch = find_property(settings, 'os.arch')

    version_is_supported = re.search("^(1.8)", version)
    arch_is_supported = re.search("^(x86|amd64)", arch)

    if version_is_supported and arch_is_supported:
        return java

    print("Unsupported java! version:%s arch:%s" % (version, arch))
    usage(argparser)

def get_configuration_variable(args, name, label):
    vars(args)

    value = vars(args)[name]
    if name != 'password':
        if value:
            print("%s: %s" % (label, value))
        else:
            value = input("%s: " % label)
    else:
        if value:
            print("%s: *****" % label)
        else:
            value = getpass.getpass()
    return value

def parse_configuration(argparser):
    class configuration: pass
    args = argparser.parse_args()

    configuration.java = find_java(argparser)
    configuration.server = get_configuration_variable(args, 'host', "IPMI host")
    configuration.username = get_configuration_variable(args, 'username', "Username")
    configuration.password = get_configuration_variable(args, 'password', "Password")

    return configuration

def update_jars(server):
    base = jarBase.format(server)
    system = platform.system()
    if system == "Linux":
        natives = "Linux_x86_"
        path = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    elif system == "Windows":
        natives = "Win"
        path = os.environ.get("LOCALAPPDATA")
    elif system == "Darwin":
        natives = "Mac"
        path = os.path.expanduser('~/Library/Application Support')
    else:
        raise Exception("OS not supportet: " + system)
    natives += platform.architecture()[0][:2] + ".jar"
    path = os.path.join(path, "jviewer-starter")

    if not os.path.exists(path):
        os.makedirs(path)
    for jar in ["JViewer.jar", "JViewer-SOC.jar", natives]:
        jar_path = os.path.join(path, jar)
        if not os.path.exists(jar_path):
            print("downloading %s -> %s" % (base + jar, jar_path))
            urlretrieve(base + jar, jar_path)
            if jar == natives:
                print("extracting %s" % jar_path)
                with zipfile.ZipFile(jar_path, 'r') as natives_jar:
                    natives_jar.extractall(path)

    return path

def get_java_options(path):
    java_options = ["-Djava.library.path=%s" % path]
    if os.environ.get('JVIEWER_JAVA_OPTIONS'):
        java_options.extend(os.environ.get('JVIEWER_JAVA_OPTIONS').split(' '))
    return java_options

def run_jviewer(configuration):
    server = configuration.server
    path = configuration.path

    credentials = {"WEBVAR_USERNAME": configuration.username, "WEBVAR_PASSWORD": configuration.password}

    loginRequest = Request(loginUrl.format(server))
    loginRequest.data = urlencode(credentials).encode("utf-8")
    loginResponse = urlopen(loginRequest).read().decode("utf-8")
    sessionCookie = re.search("'SESSION_COOKIE' : '([a-zA-Z0-9]+)'", loginResponse).group(1)

    jnlpRequest = Request(jnlpUrl.format(server))
    jnlpRequest.add_header("Cookie", "SessionCookie=%s" % sessionCookie)
    try:
        jnlpResponse = urlopen(jnlpRequest).read().decode("utf-8")
    except IncompleteRead as e:
        # The server sends a wrong Content-length header. We just ignore it
        jnlpResponse = e.partial.decode("utf-8")

    args = [configuration.java]
    args.extend(get_java_options(path))
    args.append("-cp")
    args.append(os.path.join(path, "*"))
    args.append(mainClass)
    args += re.findall("<argument>([^<]+)</argument>", jnlpResponse)

    print(" ".join(args))
    subprocess.call(args)

if __name__ == "__main__":
    print("Starting jviewer")
    argparser = argparse.ArgumentParser(description='Download and open the JViewer remote console',
        epilog='JViewer does not support Java newer than Java 8, and a JRE with x86 32/64-bit architecture must be installed. You can override the system default java with environment variable JVIEWER_JAVA_HOME.')
    argparser.add_argument('--host', nargs='?', help='the hostname or IP address of the IPMI server')
    argparser.add_argument('--username', nargs='?', help='the IPMI username')
    argparser.add_argument('--password', nargs='?', help='the IPMI password')

    configuration = parse_configuration(argparser)
    configuration.path = update_jars(configuration.server)
    run_jviewer(configuration)
