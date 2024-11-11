---
title: 'About the Android Makers app, security and google-services.json'
excerpt: '...'
publishDate: 2022-05-06T13:45:38.512Z
image: '~/assets/images/2022-05-06_about-the-android-makers-app-security-and-google-servicesjson/3nQMK1bsA.png'
---

[Android Makers](https://androidmakers.fr/) is over! With over 650 participants and 50 sessions over 2 days in Paris, it was a lot of fun! It was nice to see everyone in person again and discuss all the Android things (and 🍻 too)!

This year, we decided to rewrite the Android app ([github](https://github.com/paug/AndroidMakersApp)) in Jetpack Compose and this too was a lot of fun 😃! We got a functional app in no time and [sent it out for public scrutiny](https://twitter.com/martinbonnin/status/1516377118355111936). We got a lot of feedback and contributions (did I mention this community rocks? 🤘💙)!

This is the story of how (and why) we made our `google-services.json` public so that anyone could easily contribute.

## About google-services.json

Whenever you setup a Firebase project, `google-services.json` comes up pretty quickly in the installation instructions. You usually download it from the Firebase console:

!\[Screenshot 2022-04-29 at 18.53.25.png\](https://cdn.hashnode.com/res/hashnode/image/upload/v1651251219633/E61JnkN3U.png align="left")

If you open it, you'll find something like this (some values redacted although I'm not 100% sure why, more on that later):

```json
{
  "project_info": {
    "project_number": "378302699578",
    "project_id": "openfeedback-am-2022",
    "storage_bucket": "openfeedback-am-2022.appspot.com"
  },
  "client": [
    {
      "client_info": {
        "android_client_info": {
          "package_name": "fr.androidmakers"
        }
      },
      "api_key": [
        {
          "current_key": "[redacted]"
        }
      ]
    }
  ],
  "configuration_version": "1"
}
```

As you can see, there's something called `api_key` up there. That sounds pretty secret so certainly it's a good idea to hide it, right? Well... turns out it's not secret at all.

## Your Android API key is not secret!

Because your app needs your API key at runtime, the API key must be accessible somewhere in the app. So really it can't be secret. To prove it, let's try to retrieve it.

Start by doing a [google search for the Android Makers app apk](https://www.google.com/search?q=fr.paug.androidmakers+apk&oq=fr.paug.androidmakers+apk). This takes you to an ApkPure website that allows you to download the apk:

!\[Screenshot 2022-04-29 at 19.15.21.png\](https://cdn.hashnode.com/res/hashnode/image/upload/v1651252524982/f96rPW-4L6.png align="left")

A click and and a few downloaded MB later, you can open that APK in the Android Studio APK analyzer (Build -\> Analyze APK...). Look for a resource that looks like an API key. This `google_api_key` string sounds like a good candidate 🙃:

!\[Screenshot 2022-04-29 at 19.34.49.png\](https://cdn.hashnode.com/res/hashnode/image/upload/v1651253727280/rX9obkbQ1.png align="left")

Yup, zoom a little bit... That's the one! So I'm not sure why I redacted it above. Certainly because everything is made to make you believe this should be treated as a secret.

## Scary warnings

If you ever commit such an API key to Github, all the repository admins will receive an email along these lines:

!\[Screenshot 2022-04-29 at 19.41.03.png\](https://cdn.hashnode.com/res/hashnode/image/upload/v1651254177886/98\_vuJSyi.png align="left")

Well, that's scary 🙀...

Same thing if you publish an app to the Google play that contains your API key in Kotlin code:

!\[Screenshot 2022-04-22 at 11.02.28.png\](https://cdn.hashnode.com/res/hashnode/image/upload/v1651254315645/7LvuWI53Q.png align="left")

This is also scary 😱...

Why all these warnings if the API key can be retrieved in a few minutes by any malicious user? That remains a mystery to me. My current guess is that there's no way to distinguish between a client key and a server key so that warning is sent to anyone indiscriminately. If someone can see of a good reason to show these warnings for an Android API key, please tell me so I can edit this article and redact everything for good 😅 (and invalidate all the things too!).

## Developing in the open

After [browsing the web a bunch](https://stackoverflow.com/questions/37358340/should-i-add-the-google-services-json-from-firebase-to-my-repository), realising that [there was an official answer in the firebase forums](https://groups.google.com/g/firebase-talk/c/bamCgTDajkw/m/uVEJXjtiBwAJ) (**edit**: and it's even in the [official Firebase documentation](https://firebase.google.com/docs/projects/learn-more#config-files-objects) as [@zsmb13 made me realize later](https://twitter.com/zsmb13/status/1524010043779211267)) and double checking that the values were in the apk anyway, we decided to ignore the scary warnings, stop living in fear (🤘) and [commit our `google-services.json`](https://github.com/paug/AndroidMakersApp/pull/100)!

Now anyone can develop for the App using the real data. Special thanks to [`@underwindfall`](https://github.com/underwindfall), [`@R4md4c`](https://github.com/R4md4c) and [`@oldergod`](https://github.com/oldergod) for their awesome contributions 💙!

## What could go wrong?

Assuming someone has your Android API key. What can they do with it?

In our case, the main thing was using our Firestore instance and using our quota. We could imagine someone developing their own service squatting our Firestore instance and therefore not paying the bill at the end of the month 💸.

While technically possible, I'm not sure how practical that would be. Such a service would be dependant on a completely foreign infra and any change would break it almost instantly. I'm not aware any such attack has happened already but maybe it's a matter of time...

## Additional (actual) restrictions 🔐

The good news is that the [Google Cloud console allows to restrict the API keys](https://cloud.google.com/docs/authentication/api-keys#api_key_restrictions) 🎉

### Platform restrictions

You can restrict your API key per platform:

!\[Screenshot 2022-04-29 at 20.11.41.png\](https://cdn.hashnode.com/res/hashnode/image/upload/v1651255957380/g7ivn5SmP.png align="left")

In the example above, we restricted the API key to only be callable from Android apps. As [@RickClephas points out on Twitter](https://twitter.com/RickClephas/status/1524079729783066625), this works by using two HTTP headers: `X-Android-Package` and `X-Android-Cert`. So it's not bullet proof but it's still something.

### APIs restrictions

In addition to platforms, you can also restrict your API key to some APIs:

!\[4V4UH3LUW.png\](https://cdn.hashnode.com/res/hashnode/image/upload/v1651837353169/VxVXKzVe3.png align="left")

This makes sure no other APIs can be used so it's an additional safety. Make sure to include `Firebase Installations API` and `Token Service API` or your app will stop working after a few calls.

If your feedback was not counted during Android Makers, this is what happened 😅. Thanks to @[Hugo Gresse](@HugoGresse) and [`@GerardPaligot`](https://github.com/GerardPaligot) for catching this!

## Conclusion

You can hide your Android API key from Github but this is not going to prevent anyone to get it. If you need to share it with colleagues or your community, it should be pretty safe to commit it despite all the scary warnings.

At the end of the day, security is never a "yes" or "no" kind of question and has more of a continuum of answers. Some might argue that despites all the flaws, hiding your API key from GitHub is still making it harder to retrieve and that's very true. It's also very true that every security measure has a cost, either in terms of raw dollars or in terms of developer experience.

Of all the possibilities:

- Add [GCP API key restrictions](https://cloud.google.com/docs/authentication/api-keys#api_key_restrictions)
- Fine tune your [Firestore security rules](https://firebase.google.com/docs/firestore/security/get-started)
- Check your app integrity with something like [Firebase App Check](https://firebase.google.com/docs/app-check)
- Obfuscate your client code with something like [DexGuard](https://www.guardsquare.com/dexguard)
- Implement server side rate limiting and fraud detection
- Hide your API key from Github

I'd argue that hiding your API key from Github is the one with the worst cost/security ratio.
If you're relying on that for your security, you'd better add API key restrictions and double check your Firestore rules instead.

> Note: none of the above applies to server API keys of course. If your API keys doesn't end up in a client, make sure to keep them secure in the depths of your infra.

_This article was edited on May 10th to add a note about the Firebase official doc, the `X-Android-Package` and `X-Android-Cert` headers and rework the conclusion to display more possible solutions._

_Many thanks to [Dorian Cussen](https://twitter.com/doriancussen) and [Edouard Marquez](https://www.edouard-marquez.me/) for proof reading this article_

_Cover image background by [Claire Tresse](https://flic.kr/p/KjcUHo)_
