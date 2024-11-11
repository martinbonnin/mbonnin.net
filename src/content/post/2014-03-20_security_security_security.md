---
title: 'Security, Security, Security!'
excerpt: 'HTTPS is now the defaultFollowing recent advice, this website now uses an encrypted connection. You can browse all the wonderful content here (including rabbits) without (theorically)...'
publishDate: 2014-03-20T00:00:00Z
image: '~/assets/images/2014-03-20_security_security_security/thumbnail.jpg'
---






# HTTPS is now the default 

Following [recent advice](http://arstechnica.com/tech-policy/2014/03/ed-snowden-at-sxsw-theyre-setting-fire-to-the-future-of-the-internet/), this website now uses an encrypted connection. You can browse all the wonderful content here (including rabbits) without (theorically) being spied on.

I used a [startssl](https://www.startssl.com/) certificate. Startsll gives free certificates and last time I checked, their Certificate Authorities were bundled in major web browsers, meaning no scary warning. If you have some, please tell me. 

# PGP key 

I also took this opportunity to publish my PGP public key. You can find it here: <a href="../../pgp.txt">http://mbonnin.net/pgp.txt</a>

# Others 

The OVH web hosting I was using previously does not allow custom SSL certificates so I moved to a [VPS classic 1 instance](http://www.ovh.com/fr/vps/vps-classic.xml). At 2€/month it's not that expensive and much cheaper than a micro EC2 instance. Let's see how it behaves...

Edit 15/04/2014: Turned out HTTPS was not enough to prevent eavesdropping. The instance has been patched last week to fix the [heartbleed bug](http://en.wikipedia.org/wiki/Heartbleed).

<hr>
Lock photo by [Thomas](https://flic.kr/p/7ywqZ6)

