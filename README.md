# jviewer-starter

Script to download and start the JViewer remote console application. It has become increasingly difficult to execute Java Web Start applications, this script helps alleviate the pain and frustration. Tested on my AsrockRack D1541D4U-2T8R.

Furthermore, the JViewer version in the latest BMC firmware (as of 2022) requires Java 8 and does not work on architectures other than x86 (Intel/AMD).

This was a problem for me when I got my new M1-based Mac. I found this excellent script (forked from [https://github.com/arbu/jviewer-starter](https://github.com/arbu/jviewer-starter) -- thank you!), and I modified it to work with a non-default Java installation so that a x64 Java can be started (rather than an Apple Silicon aarch64 Java). This will run under Rosetta. However, since Rosetta will most likely not be around forever, I also wrapped the script in a Docker container (built with x64 architecture). The Docker container can be run on any architecture via Docker, hopefully providing somewhat more "future-proofness" if/when Rosetta is removed from MacOS. The Docker container expects a x-server (referenced by the `DISPLAY` env variable), and therefore also requires XQuartz to be installed on MacOS.

I use MacOS and have tested both the initial script and the docker container. I have not extensively tested this on Linux hosts. Zero testing has been performed on Windows, good luck there.

## Installation

* Install Java 8 for x64 (other architectures and newer JREs not supported by JViewer!). Examples:
    * [Adoptium/Temurin](https://adoptium.net/temurin/releases/?version=8)
    * [Azul](https://www.azul.com/downloads/)
* Install [Docker](https://www.docker.com/products/docker-desktop/) (optional, if you do not want to install Java locally)
* Install [XQuartz](https://www.xquartz.org/) (needed if using Docker and MacOS)

### MacOS:

I recommend symlinking the scripts to `/usr/local/bin` (or another location in your `PATH`) so they can be easily started:

```bash
ln -s path/to/jviewer-starter/jviewer-starter.py /usr/local/bin/jviewer-starter
ln -s path/to/jviewer-starter/jviewer-docker.sh /usr/local/bin/jviewer-docker
```

#### MacOS (Intel):
```bash
brew install zulu8
```

#### MacOS (Apple Silicon)
```bash
export ZULU_VERSION=zulu8.64.0.19-ca-jdk8.0.345-macosx_x64
curl -L "https://cdn.azul.com/zulu/bin/${ZULU_VERSION}.tar.gz" -o /tmp/${ZULU_VERSION}.tar.gz
pushd /tmp
tar -xzvf ${ZULU_VERSION}.tar.gz
mv /tmp/${ZULU_VERSION}/zulu-8.jdk /tmp/${ZULU_VERSION}/zulu-8-x64.jdk
sudo mv /tmp/${ZULU_VERSION}/zulu-8-x64.jdk /Library/Java/JavaVirtualMachines/
sudo xattr -r -d com.apple.quarantine /Library/Java/JavaVirtualMachines/zulu-8-x64.jdk
sudo chown -R root:wheel /Library/Java/JavaVirtualMachines/zulu-8-x64.jdk
rm -rf /tmp/${ZULU_VERSION}*
export ZULU_VERSION
popd

# then set the java version for JViewer
export JVIEWER_JAVA_HOME=/Library/Java/JavaVirtualMachines/zulu-8-x64.jdk/Contents/Home
```

### Other Operating Systems:

gl;hf


## Running

Run with a locally-installed Java:
```bash
jviewer-starter
jviewer-starter --host [ip|hostname to server] --username [ipmi username] --password [ipmi password]
```

Run via Docker:
```bash
jviewer-docker
jviewer-docker --host [ip|hostname to server] --username [ipmi username] --password [ipmi password]
```

## Issues

XQuarts 2.8.2 has [a known issue](https://github.com/XQuartz/XQuartz/issues/31) in which GUI background elements inverse their colors upon mouse movement. I have applied a recommended fix via Java properties injected in `JVIEWER_JAVA_OPTIONS`. This only affects JViewer via Docker.


## References:

* [http://mamykin.com/posts/running-x-apps-on-mac-with-docker/](http://mamykin.com/posts/running-x-apps-on-mac-with-docker/)
* [https://cntnr.io/running-guis-with-docker-on-mac-os-x-a14df6a76efc](https://cntnr.io/running-guis-with-docker-on-mac-os-x-a14df6a76efc)
* [https://github.com/XQuartz/XQuartz/issues/31](https://github.com/XQuartz/XQuartz/issues/31)
