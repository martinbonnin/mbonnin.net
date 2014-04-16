#!/usr/bin/env bash

function usage()
{
    echo "usage:"
    echo "    install_apache.sh user@host cert_file key_file" 
    echo ""        
    echo "    cert_file is concatenation of all certificates" 
    echo "    key_file is the (possibly encrypted) keyfile. It will be decrypted before being stored stored" 

    exit 1;
}

if [[ $# -lt 3 ]]
then
    usage
fi

HOST=$1
CERT_FILE=$2
KEY_FILE=$3

(echo $CERT_FILE | grep "mbonnin.net_2014_chain.pem") || { echo "cert should be mbonnin.net_2014_chain.pem"; exit 1; }

TMPDIR=`mktemp -d tmp.apache.XXXX`

CONF_FILE=${TMPDIR}/mbonnin.net.conf
cat > ${CONF_FILE} << EOF
<VirtualHost *:80>
	ServerName http://mbonnin.net/
#    Redirect permanent / https://mbonnin.net/

	DocumentRoot /root/site
	<Directory />
		Options FollowSymLinks
		AllowOverride None
	</Directory>
	<Directory  /root/site>
		Options Indexes FollowSymLinks MultiViews
		AllowOverride None
		Order allow,deny
		allow from all
	</Directory>

</VirtualHost>


<IfModule mod_ssl.c>
<VirtualHost _default_:443>
	DocumentRoot /root/site
	<Directory />
		Options FollowSymLinks
		AllowOverride None
	</Directory>
	<Directory  /root/site>
		Options Indexes FollowSymLinks MultiViews
		AllowOverride None
		Order allow,deny
		allow from all
	</Directory>
    <Directory /root/site/feed>
        AddType application/rss+xml .xml
        DirectoryIndex feed.xml
    </Directory>

	SSLEngine on
	SSLCertificateFile /etc/apache2/ssl/mbonnin.net_2014_chain.pem
    SSLCertificateKeyFile /etc/apache2/ssl/mbonnin.net_2014.key
	SSLCertificateChainFile /etc/apache2/ssl/mbonnin.net_2014_chain.pem
    
	LogLevel warn
	CustomLog /var/log/apache2/access.log combined
</VirtualHost>
</IfModule>
EOF

INSTALL_FILE=${TMPDIR}/install.sh
cat > ${INSTALL_FILE} << EOF
sudo aptitude install apache2
cd /etc/apache2/mods-enabled/
ln -fs ../mods-available/ssl.conf .
ln -fs ../mods-available/ssl.load .

cd ~
mv mbonnin.net.conf /etc/apache2/sites-enabled/
mkdir -p /etc/apache2/ssl/
mv mbonnin.net_2014_chain.pem /etc/apache2/ssl/
#decrypt if needed
openssl rsa -in mbonnin.net_2014.key -out /etc/apache2/ssl/mbonnin.net_2014.key
rm mbonnin.net_2014.key
/etc/init.d/apache2 restart
EOF

cp ${KEY_FILE} ${TMPDIR}/
cp ${CERT_FILE} ${TMPDIR}/

scp ${TMPDIR}/* $HOST:

rm -rf ${TMPDIR}

ssh $HOST "chmod +x install.sh; ./install.sh"

