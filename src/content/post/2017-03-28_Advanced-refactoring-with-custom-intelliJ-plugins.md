---
title: 'Advanced refactoring with custom intelliJ plugins'
excerpt: 'Moving from AndroidAnnotations to ButterKnife using automatic processing from a custom intellij plugin'
publishDate: 2017-03-28T00:00:00Z
image: '~/assets/images/2017-03-28_Advanced-refactoring-with-custom-intelliJ-plugins/ij.png'
---

---

The process allowed us to refactor \> 50 classes at once with minimal human intervention. The case described here is fairly specific to our own development style and conventions but you can reuse the techniques to manipulate your own java classes and automate a lot of repetitive coding tasks. The full source code to our plugin is available [on github](https://github.com/dailymotion/aa2bk) and can be as a base for all kinds of refactoring plugins.

### The problem

At Dailymotion, we started working on the Android app back in 2012. At the time, we went for AndroidAnnotation as the swiss army knife of annotation processing. It works quite well and allows for more concise code, but over the years and as the apps became more complex, we began to find some things annoying:

- Lack of focus, AndroidAnnotations has a very rich feature set but we mainly use it for view injection so we don't really care about `@Backround` or `@Rest`.
- We use RxJava for async task handling and really don't want new devs to start using `@Background` just because they can. Same for `@Rest`
- More generally, it looks like more devs are familiar with ButterKnife nowadays.
- Having to append an underscore everytime you use a class is a pain, I'm not counting the number of times I referenced a view without its final `'_'`.

So we decided to move to Butterknife for View injection. We needed to do something like:

Move from AndroidAnnotations:

```java
@EviewGroup(R.layout.myview)
public class MyView extends View {
    @ViewById
    TextView textView;

    @AfterViews
    public void afterViews() {
        textView.setText("hello world");
    }
}
```

to ButterKnife:

```java
public class MyView extends View {
    @BindView(R.id.textView)
    TextView textView;

    @Override
    protected void onFinishInflate() {
        super.onFinishInflate();

        ButterKnife.bind(this);
        textView.setText("hello world");
    }

    public static MyView build(Context context) {
        return (MyView)LayoutInflater.from(context).inflate(R.layout.myview, null);
    }
}
```

The transformations are simple:

- create a static method that will inflate the appropriate layout file.
- move the contents of `@AfterView` to `onFinishInflate`
- replace `@ViewById` by `@BindView`

If you have a single class, it's fairly easy to do but doing this over a large codebase is boring and error prone.

Neither JavaParser nor Lombok can preserve the whitespaces in your java files, which is a must have in this case. It turned out IntelliJ has a quite powerful Java [AST](https://en.wikipedia.org/wiki/Abstract_syntax_tree) implementation and can also work with XML. And it's the IDE we use everyday for our Android coding so we can leverage that too.

### How it works

The main entry point of the plugin is the `actionPerformed` method:

```java
public void actionPerformed(AnActionEvent event) {
    mProject = event.getData(PlatformDataKeys.PROJECT);
    WriteCommandAction.runWriteCommandAction(mProject, () -> {
        Util.traverseFiles(mProject, new HashSet<>(Arrays.asList(".java")), psiFile -> {
            for (PsiElement psiElement: psiFile.getChildren()) {
                if (psiElement instanceof PsiClass) {
                    if (Util.getAnnotation(psiElement, "EViewGroup") != null) {
                        processClass((PsiClass) psiElement);
                    }
                }
            }
        });
        Util.traverseFiles(mProject, new HashSet<>(Arrays.asList(".java", ".xml")), psiFile -> {
            processIdentifiers(psiFile);
        });
    });
}
```

- `WriteCommandAction.runWriteCommandAction`: this makes the IDE aware that we are going to actually change code. This way, you can automagically undo your huge refactoring if you want to.
- Then we traverse all the project files twice:

1. First time to transform all the classes
2. Second time to change all the usages of the classes. `MyView_.build(context)`becomes `MyView.build(context)`. Note that it also changes the XML occurences too :-) !

### IntelliJ PSI (Program Structure Interface)

[PSI](http://www.jetbrains.org/intellij/sdk/docs/basics/architectural_overview/psi_files.html) reprensents your whole files as trees where you can edit individual nodes. You can think of it as a sort of DOM for Java.

- determine if a given field has a `ViewById` annotation:

```java
for (PsiElement element : annotationList) {
    if (element.getText().equals("@ViewById")) {
        annotation = (PsiAnnotation) element;
        break;
    }
}
```

- replace the `ViewById` annotation with `BindView`:

```java
String a = String.format("@BindView(R.id.%s)", fieldName);
PsiAnnotation newAnnotation = JavaPsiFacade.getInstance(mProject).getElementFactory().createAnnotationFromText(a, psiField);
annotation.replace(newAnnotation);
```

- adding a `onFinishInflate` method:

```java
body = "@Override" +
            " protected void onFinishInflate() {" +
            "super.onFinishInflate();" +
            "}";
onFinishInflatePsiMethod = JavaPsiFacade.getElementFactory(mProject).createMethodFromText(body, psiClass);
onFinishInflatePsiMethod = (PsiMethod) psiClass.add(onFinishInflatePsiMethod);
```

And more... You can basically transform your files the way you want. In our case, click the 'Dailymotion' -\> 'Do some magic' menu to remove all your AndroidAnnotations.

### What's next

Since I'm going to use this plugin exactly once in my life, I did not spend time doing a nice user interface showing the progress, etc... But it's something doable. If you enforce common devstyles and patterns, then moving to new frameworks becomes much easier. We hope to see plenty of refactoring plugins soon to refactor all the things :) !
By [Martin Bonnin](https://medium.com/@mbonnin) on [March 28, 2017](https://medium.com/p/d0ca4d21bdf1).

[Canonical link](https://medium.com/@mbonnin/advanced-refactoring-with-custom-intellij-plugins-d0ca4d21bdf1)

Exported from [Medium](https://medium.com) on November 9, 2024.
