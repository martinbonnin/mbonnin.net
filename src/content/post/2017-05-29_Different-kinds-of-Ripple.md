---
title: 'Different kinds of Ripple'
publishDate: 2017-05-29T00:00:00Z
image: '~/assets/images/2017-05-29_Different-kinds-of-Ripple/ripple.jpg'
---

### The regular Ripple

```
<ripple xmlns:android="http://schemas.android.com/apk/res/android"
    android:color="#f00">
    <item android:id="@android:id/mask">
        <color android:color="#ff0000ff" />
    </item>
</ripple>
```

![](../../assets/images/2017-05-29_Different-kinds-of-Ripple/1*xgqluEEQKHgDnYoeA6j35w.gif)

### The borderless Ripple

```xml
<ripple xmlns:android="http://schemas.android.com/apk/res/android"
    android:color="#f00">
</ripple>
```

![](../../assets/images/2017-05-29_Different-kinds-of-Ripple/1*H5OgZtWjBTniAiBLjnkooA.gif)

### The semi-transparent Ripple

```xml
<ripple xmlns:android="http://schemas.android.com/apk/res/android"
    android:color="#f00">
    <item android:id="@android:id/mask">
        <color android:color="#8000ffff" />
    </item>
</ripple>
```

![](../../assets/images/2017-05-29_Different-kinds-of-Ripple/1*GzqxaUf9FpxUsNLEYITqjA.gif)

### The completely transparent Ripple (hint: not super useful)

```xml
<ripple xmlns:android="http://schemas.android.com/apk/res/android"
    android:color="#f00">
    <item android:id="@android:id/mask">
        <color android:color="#0000ffff" />
    </item>
</ripple>
```

![](../../assets/images/2017-05-29_Different-kinds-of-Ripple/1*H2tHx2PythMTYc4La_zqMg.png) By [Martin Bonnin](https://medium.com/@mbonnin) on [May 29, 2017](https://medium.com/p/d8aa92f5a05a).

[Canonical link](https://medium.com/@mbonnin/different-kinds-of-ripple-d8aa92f5a05a)

Exported from [Medium](https://medium.com) on November 9, 2024.
