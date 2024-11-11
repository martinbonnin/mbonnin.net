---
title: 'Publishing a maven artifact 1/3: glossary'
excerpt: 'Warming up...'
publishDate: 2019-06-05T00:00:00Z
image: '~/assets/images/2019-06-05_Publishing-a-maven-artifact-1-3--glossary/1*Hg-VsBa-b2SGJO1FxXGidg.jpeg'
---

### Publishing a maven artifact 1/3: glossary

*This is the first article in a series describing how I started distributing my android/kotlin libraries. I am quite new to the subject and these articles do not pretend to be exhaustive yet they should be a good introduction for anyone who has been developing for a time and wants to make his/her software more broadly available. Especially, this first article tries to decode a lot of confusion around the different actors of the ecosystem.*

[*Part 2/3*](https://proandroiddev.com/publishing-a-maven-artifact-2-3-jcenter-or-mavencentral-e0f82ba3f473)*dives into the jcenter vs mavenCentral debate.*

[*Part 3/3*](https://medium.com/p/bd661081645d)*describes a step-by-step solution for publishing your android/kotlin project to MavenCentral.*

### The common ground

Let's start by reviewing what exactly maven is and why we should care.
![](../../assets/images/2019-06-05_Publishing-a-maven-artifact-1-3--glossary/1*5RE1ZBWIc6jNEhI75-X05w.png)

#### Maven

M[aven](https://maven.apache.org/) (or Apache Maven, [wikipedia](https://en.wikipedia.org/wiki/Apache_Maven)) is an open source build system, developed by the Apache foundation and mostly used for java projects.   
It uses pom files that describe the structure of the project and its dependencies. Together with other artifacts like jar files or source.jars, this defines a format for hosting them and make them available for reuse.   
These files are hosted on a web server typically using the following structure:  
*https://baseurl/{groupId}/{packageId}/{version}/{artifact}* For an example, okhttp will be at <https://repo1.maven.org/maven2/com/squareup/okhttp3/okhttp/3.9.1/okhttp-3.9.1.jar>

#### Pom file

The [pom file](https://maven.apache.org/guides/introduction/introduction-to-the-pom.html) is a XML file describing how to build the project, its dependencies as well as some metadata about the authors, licence, version control. For an example, the [okhttp pom file](https://repo1.maven.org/maven2/com/squareup/okhttp3/okhttp/3.9.1/okhttp-3.9.1.pom).

#### Artifact

Artifacts are the results of a project compilation. For jvm projects, this is typically .jar files, sources.jar, or .war.

#### GroupId

The groupId is the namespace where artifacts are store. Usually it is a reversed domain. For an example [com.squareup.okhttp3](https://repo1.maven.org/maven2/com/squareup/okhttp3/).

#### ArtifactId

This is the name of the artifact. For an example [okhttp](https://repo1.maven.org/maven2/com/squareup/okhttp3/okhttp/).

#### Snapshot

A snapshot (e.g 0.1.2-SNAPSHOT) is the version of artifacts while they're still being worked on. If you download the same snapshot version at two different times, you might get different binaries. Snapshots typically cannot be hosted on the main repositories but have their own.

#### MavenLocal

A local repository simply serving artifacts over the filesystem. Usually it resides on your machine at `~/.m2`

#### Repository

It can refer to two things:

* A complete repository like mavenCentral or jcenter hosting a lot of packages
* A subpart of a complete repository matching a groupId. If you manage a groupId on sonatype or Bintray, they will be shown as "repositories"

### Sonatype ecosystem

![](../../assets/images/2019-06-05_Publishing-a-maven-artifact-1-3--glossary/1*Jt1YIiEgXPKZ0vkiXDKrOA.jpeg)

#### Sonatype

[Sonatype](https://www.sonatype.com/about) is the company hosting MavenCentral. They are core contributors to the maven build system. They also have a commercial offering for (amongst other things) hosting your own repository and/or monitoring your CI/CD.

#### MavenCentral

[MavenCentral](https://central.sonatype.org/pages/about.html) is a repository hosted by Sonatype for open source artifacts. For an exemple, you can find the [okhttp](https://square.github.io/okhttp/) files [here](https://repo1.maven.org/maven2/com/squareup/okhttp3/okhttp/3.9.1/).   
To have your artifacts listed on MavenCentral, you first need to upload them on OSSRH before promoting them to MavenCentral.  
Browse at: <https://repo1.maven.org/maven2>   
Search at: <https://search.maven.org>

*Note that MavenCentral is quite different from Maven, the build tool and that there are a lot of other maven repositories out there like jcenter (see below).*

#### OSSRH

The [Open Source Software Repository Hosting](https://oss.sonatype.org) is the staging repository before artifacts are promoted to mavenCentral. To upload artifacts there, [you will need to verify](https://central.sonatype.org/pages/ossrh-guide.html) that you own your groupId, most of the time using a TXT DNS record.  
Browse at: <https://oss.sonatype.org/content/repositories/releases/>

#### Sonatype snapshots repositories

Snapshot can typically not be uploaded to MavenCentral but once you upload them to OSSRH, they become available at <https://oss.sonatype.org/content/repositories/snapshots/>

#### Nexus

Nexus is a suite of tools and software developed by Sonatype to host artifacts. MavenCentral [uses](https://central.sonatype.org/pages/producers.html) a Nexus instance to host open source artifacts.

### Jfrog ecosystem

![](../../assets/images/2019-06-05_Publishing-a-maven-artifact-1-3--glossary/1*pLAJRTVvJbmgSjtaz9epfA.png)

#### Jfrog

JFrog is the company behind JCenter and artifactory.

#### JCenter

JCenter is the MavenCentral of JFrog. It is public a maven repository for open source artifacts. To have your artifacts listed on MavenCentral, you first need to upload them to Bintray.  
Browse at: [https://jcenter.bintray.com/](http://jcenter.bintray.com/)  
Search at: [https://bintray.com](https://bintray.com/bintray)

#### OJO

[oss.jfrog.org](http://oss.jfrog.org/) is an artifactory instance used to serve snapshots.  
Browse at: <https://oss.jfrog.org/artifactory/libs-snapshot/>  
Search at: <https://oss.jfrog.org/>

#### Artifactory

Artifactory is a suite of tools and software developed by JFrog to host artifacts aimed at development. It can be deployed on premises and allows snapshots of artifacts.

#### Bintray

Bintray is a suite of tools and software developed by JFrog to host artifacts aimed at distribution. It uses a fast CDN for faster download. JCenter uses Bintray.  
Bintray doesn't verify groupId ownership which [has led to compromised artifacts in the past](https://blog.autsoft.hu/a-confusing-dependency/).

### Gradle plugins

![](../../assets/images/2019-06-05_Publishing-a-maven-artifact-1-3--glossary/1*-C_M_N8VzS7Sf7pswbZaKQ.png)

#### Gradle 'maven'

The ['maven' plugin](https://docs.gradle.org/current/userguide/maven_plugin.html) is the "old" plugin used to publish to mavenLocal or a remote maven repository.

#### Gradle 'maven-publish'

The ['maven-publish' plugin](https://docs.gradle.org/current/userguide/publishing_maven.html) is the "new" plugin used to publish to mavenLocal or a remote maven repository. It's interesting to note that in 2013, this plugin [was already considered "new"](https://chris.banes.dev/2013/08/27/pushing-aars-to-maven-central/). It's still unclear what benefits it brings compared to the old version. Some users have reported [issues with signing](https://discuss.gradle.org/t/how-to-publish-artifacts-signatures-asc-files-using-maven-publish-plugin/7422) while others just [continue using the old 'maven' plugin](https://github.com/vanniktech/gradle-maven-publish-plugin/blob/master/src/main/kotlin/com/vanniktech/maven/publish/MavenPublishPluginExtension.kt#L28).

#### Gradle 'signing'

The ['signin' plugin](https://docs.gradle.org/current/userguide/signing_plugin.html) is used to sign artifacts. This is required by Sonatype OSSRH.

#### Dcendents 'android-maven-gradle-plugin'

The [dcendents](https://github.com/dcendents/android-maven-gradle-plugin) plugin is a third party plugin that allows publishing Android .aar files.

#### Bintray 'gradle-bintray-plugin'

The [gradle-bintray-plugin](https://github.com/bintray/gradle-bintray-plugin) is provided by Bintray.

#### Codearte 'gradle-nexus-staging-plugin'

[Codearte plugin](https://github.com/Codearte/gradle-nexus-staging-plugin) allows to promote Sonatype repositories from the command line without having to login on <https://oss.sonatype.org>.

#### Marcphilipp 'nexus-publish-plugin'

[Marcphilipp plugin](https://github.com/marcphilipp/nexus-publish-plugin/) allows you to specify the staging repository before uploading to OSSRH or any other Nexus repository.

#### Vanniktech 'gradle-maven-publish-plugin'

[Vanniktech plugin](https://github.com/vanniktech/gradle-maven-publish-plugin) allows to publish kotlin and android code and upload source and javadoc automatically. It is the plugin [used by okhttp](https://github.com/square/okhttp/blob/master/build.gradle#L43) and since I usually trust this team, I'm using this plugin in part 3/3 of this series to show how to publish artifacts as easily as possible.

### Wrapup

That was a lot!

And this list is never near exhaustive. There are other repositories and the amount of third party gradle plugins is overwhelming each one supporting slightly different use cases:

* Android AARs
* Kotlin
* Source jar generation
* Artifact Signing
* Javadoc generation
* Snapshots
* Bintray vs OSSRH (jcenter vs mavenCentral)

This last point will be the topic of the next article in this series. [Meet you there](https://proandroiddev.com/publishing-a-maven-artifact-2-3-jcenter-or-mavencentral-e0f82ba3f473) !

By [Martin Bonnin](https://medium.com/@mbonnin) on [June 5, 2019](https://medium.com/p/bc0068a440e0).

Photo: "Too much packaging material" by [PlaxcoLab](https://flic.kr/p/5VWw3b)

[Canonical link](https://medium.com/@mbonnin/publishing-a-maven-artifact-1-3-glossary-bc0068a440e0)

Exported from [Medium](https://medium.com) on November 9, 2024.
