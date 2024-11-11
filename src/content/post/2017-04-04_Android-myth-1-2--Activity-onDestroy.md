---
title: 'Android myth 1/2: Activity.onDestroy()'
excerpt: 'Please prove me wrong...'
publishDate: 2017-04-04T00:00:00Z
image: '~/assets/images/2017-04-04_Android-myth-1-2--Activity-onDestroy/hammer.jpg'
---

There's a common conception that `onDestroy`marks the end of an Android activity so that you need to cancel all your subscribers/asynctasks/whatever as soon as onDestroy fires.

I believe this is mainly due to the Fragments implementations and the dreaded `IllegalStateException` but I have always wondered whether you could maintain a strong reference to an activity after `onDestroy` and do UI stuff there.

So I did a little test there: <https://github.com/martinbonnin/TestOnDestroy>

```java
private Runnable mChangeContentViewRunnable = new Runnable() {
    @Override
    public void run() {
        Log.d(TAG, "callback!");
        getResources();
        setContentView(new TextView(MainActivity.this));
    }
};

@Override
protected void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);
    Log.d(TAG, "onCreate");
    setContentView(new FrameLayout(this));

}

@Override
public void onBackPressed() {
    super.onBackPressed();
    Log.d(TAG, "onBackPressed");
    finish();
}

@Override
protected void onDestroy() {
    Log.d(TAG, "onDEstroy");
    new Handler().postDelayed(mChangeContentViewRunnable, 3000);
    super.onDestroy();
}
```

Turns out it didn't crash... Am I missing something ?
By [Martin Bonnin](https://medium.com/@mbonnin) on [April 4, 2017](https://medium.com/p/d7f62542023d).

[Canonical link](https://medium.com/@mbonnin/android-myth-1-2-activity-ondestroy-d7f62542023d)

Exported from [Medium](https://medium.com) on November 9, 2024.
