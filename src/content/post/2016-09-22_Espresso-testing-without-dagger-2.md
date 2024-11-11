---
title: 'Espresso testing without dagger 2'
publishDate: 2016-09-22T00:00:00Z
image: '~/assets/images/2016-09-22_Espresso-testing-without-dagger-2/coffee.jpg'
---

---

A lot of apps use some local storage to store things like the number of times the app has been launched. If it's the first launch, it displays an onboarding. After a few launches, it displays a dialog asking to rate the app, etc...

This is of course very convenient but becomes a problem when trying to test because it makes the state depend on the previous launches and therefore make tests not really predictable.

Depending the size of the data needed to be stored, that could be either [android preferences](https://developer.android.com/reference/android/content/ContextWrapper.html#getSharedPreferences%28java.lang.String,%20int%29) or a Database. To make sure the app always starts in the same state, you can replace the default implementations before the test starts.

Of course dagger 2 and dependency injection is nice and all but you really don't need to pull all the dagger stuff and go all in on dependency injection to do nice functional tests on Android and decouple your classes.

```java
public class Environment {
    private static Settings sSettings;
    private static Database sDatabase;

    public static Settings getSettings() {
        if (sSettings == null) {
            sSettings = new Settings(MyApplication.get());
        }
        return sSettings;
    }

    @UsedByTestCode
    public static void setSettings(Settings settings) {
        sSettings = settings;
    }

    public static Database getDatabase() {
        if (sDatabase == null) {
            sDatabase = new Database(MyApplication.get());
        }
        return sDatabase;
    }

    @UsedByTestCode
    public static void setDatabase(Database database) {
        sDatabse = database;
    }

}
```

A few comments:

- I called the class Environment because it's global to the whole app. But you can call it the way you want, Module or Global.
- The @UsedByTestCode annotation is needed so that proguard does not remove the methods from the apk. Even if the production apk does not use them, the test apk will.
- You most certainly need a static variable to store the ApplicationContext. This is need by so many android methods and this is what MyApplication.get() does.

When you want to access a setting, you can simply do:

```java
Environment.getSettings().get("key", defaultValue)
```

### Initialization order

The main trick is when to call the Environment.setSettings() method. There are 2 ways to do it:

#### Before Activity.onCreate()

```java
@Rule
public ActivityTestRule<MainActivity> mActivityTestRule = new ActivityTestRule<MainActivity>(MainActivity.class) {
    @Override
    protected void beforeActivityLaunched() {
        super.beforeActivityLaunched();
        Environment.setSettings(new TestSettings(InstrumentationRegistry.getTargetContext()))
        Environment.setDatabase(new Database(InstrumentationRegistry.getTargetContext()))
    }
};
```

This will be called after Application.onCreate() and before Activity.onCreate() so if you have some code in Application.onCreate() that needs your singletons, this happens too late.

#### Before Application.onCreate()

For this you need to implement your own TestRunner and reference it from your build.gradle:

```groovy
testInstrumentationRunner "com.application.test.TestRunner"
```

And in TestRunner.java

```java
public class TestRunner extends AndroidJUnitRunner {
    @Override
    public void callApplicationOnCreate(Application app) {
        Environment.setSettings(new TestSettings(InstrumentationRegistry.getTargetContext()));
        Environment.setDatabase(new Database(InstrumentationRegistry.getTargetContext()));

        super.callApplicationOnCreate(app);
    }
}
```

The drawback is that your settings will not be reset between your different tests but you get the guarantee that your init is called before any of the production code.

### Proguard

In order to prevent proguard from removing all your nice test methods, you can use a specific annotation:

```java
public @interface UsedByTestCode {
}
```

And in your proguard.cfg:

```
-keepclassmembers class ** {
    @com.application.util.UsedByTestCode *;
}
```

### TestSettings implementation

We just create a shared preference called "test" that is separate from the main one and clear it every time:

```java
public class TestSettings extends Settings {
    public TestSettings(Context context) {
        super(context);
        mSharedPreferences = context.getSharedPreferences("test", MODE_PRIVATE);
        mSharedPreferences.edit()
                .clear()
                .putInt("launch_count", 50)
                .commit();
    }
}
```

### Conclusion

You can achieve something very similar to dagger with, what I believe less code, less dependencies and more clarity. Now is time to run all these nice functional test in continous integration !
By [Martin Bonnin](https://medium.com/@mbonnin) on [September 22, 2016](https://medium.com/p/3933fddeda74).

[Canonical link](https://medium.com/@mbonnin/espresso-testing-without-dagger-2-3933fddeda74)

Exported from [Medium](https://medium.com) on November 9, 2024.
