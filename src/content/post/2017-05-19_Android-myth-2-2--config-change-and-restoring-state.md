---
title: 'Android myth 2/2: config change and restoring state'
excerpt: 'Do we really need Architecture Components ?'
publishDate: 2017-05-19T00:00:00Z
image: '~/assets/images/2017-05-19_Android-myth-2-2--config-change-and-restoring-state/hammer.jpg'
---

### The problem

It's something every Android developer bumps into at some point.

* You write your activity. Everything goes well.
* The device orientation changes.
* The activity is destroyed and re-created.
* You lose all your state :-(.

That sucks !

### The complicated solution(s)

There's [a lot of documentation](https://developer.android.com/guide/topics/resources/runtime-changes.html) about how to handle this. Usually the recommendation is to save the state somewhere:

* in the Bundle.
* in retained fragments.
* in [Architecture Components](https://developer.android.com/topic/libraries/architecture/index.html) `LiveData` objects as announced recently at Google IO

These are indeed solutions but theyrequires significant effort. Serializing everything to a Bundle is especially cumbersome. Keeping retained objects is a bit better but forces you to keep that in mind all the time and handle `Loaders` or other objects which lifecycle you have to handle too.

### The simple solution

Use `android:configChanges="orientation"` !

Your activity won't be restarted and you can continue your business as usual. The onLayout() will be called and your views will resize them to match the new screen size. Remember that's the beauty of using Layouts !

### The objections

* "you cannot use orientation-dependant resources"

While technically true, I find this to actually be an advantage. Having one XML layout for landscape and another one for portrait duplicates a lot of code. It duplicates some XML code obviously but most likely some java code too. Changing a resource id in one will require the same resource id to be used in the other one without compile time safety. This is super dangerous.

* "you still need to handle configuration changes or else your users are going to be super upset"

I'm a bit confused by this one. Most of the usual config changes can be handled by just re-requesting a layout. The only alternate resources I use are for strings. So changing the phone language will restart the activity but I believe it does not happen that often.

* "There are some cases where progress is critical and you can't afford to lose it for any reason"

This is completely true for a given category of apps. Productivity apps are an example, you don't want to lose all your precious notes. Games are another example where you don't want to restart on level 1 every time. But while this is true, this is also completely unrelated to configuration changes. These kind of apps usually save their progress in the cloud or on a local database, outside the whole Android lifecycle mambo.

For other apps, that are mainly read-only, it's okay to restart from the home screen from time to time.

### Conclusion

I don't understand this level of focus on a problem that can be easily circumvented. And the new Architecture Components might actually not do any good. But maybe I'm missing something... Internet, please prove me wrong.
By [Martin Bonnin](https://medium.com/@mbonnin) on [May 19, 2017](https://medium.com/p/6388f52f0a28).

[Canonical link](https://medium.com/@mbonnin/android-myth-2-2-config-change-and-restoring-state-6388f52f0a28)

Exported from [Medium](https://medium.com) on November 9, 2024.
