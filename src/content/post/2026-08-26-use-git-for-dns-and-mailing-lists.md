---
title: 'Use git for your DNS and mailing lists'
excerpt: 'Distributed and versioned infrastructure for your organization'
publishDate: 2026-02-26T00:00:00Z
image: '~/assets/images/2026-08-26-use-git-for-dns-and-mailing-lists/thumbnail.jpg'
---

[Infrastructure as code](https://en.wikipedia.org/wiki/Infrastructure_as_code) (IaC) is great! 

Using IaC, you get:

* full visibility into what is going into your production system.
* easy contributions (git!).
* audit trails.
* notification when things change.
* backups and rollbacks when things go wrong.

IaC is not only for your FAANG-style hyper scaleup. It's easy to set up, and the benefits start at one person. If you have two persons contributing to your organization, you should use IaC for your DNS and mailing lists.

Here's how I've been doing it lately and it's been serving me well.

## DNS with OctoDNS

[OctoDNS](https://github.com/octodns/octodns) provides a set of tools & patterns that make it easy to manage your DNS records across multiple providers.

While you can also use [Terraform](https://www.terraform.io/) for your DNS, OctoDNS makes it easier to switch providers. Also has the nice bonus that you don't need to maintain a separate Terraform state. 

You can take a look at the [PAUG dns configuration](https://github.com/paug/dns/blob/9089e029dd431d9e712604b44c351b431aa1d27a/zones/paug.fr.yaml) for an example:

```yaml
---
? ''
: - ttl: 21600
    type: A
    value: 199.36.158.100
  - ttl: 21600
    type: MX
    values:
    - exchange: aspmx.l.google.com.
      preference: 1
    - exchange: alt1.aspmx.l.google.com.
      preference: 5
    - exchange: alt2.aspmx.l.google.com.
      preference: 5
    - exchange: aspmx2.googlemail.com.
      preference: 10
    - exchange: aspmx3.googlemail.com.
      preference: 10
  - ttl: 21600
    type: TXT
    values:
    - google-site-verification=CF5OccWvfQMQZwQ9n9QM2H3tpTneSYwzd9ZZay0TTDQ
    - hosting-site=website-73f72
    - v=spf1 mx include:_spf.google.com include:mx.ovh.com ~all
```

I'm not the biggest [yaml](https://noyaml.com/) fan, but for things like this, it's [good enough](https://www.bazardugrenier.com/cdn/shop/collections/david_goodenough.png?v=1739120343). 

And you can add comments!

This is all automated through GitHub Actions. A pull request creates a plan, the [merge triggers an update of the records](https://github.com/paug/dns/blob/main/.github/workflows/dns-apply.yml):

```yaml
on:
  push:
    branches: [main]

jobs:
  apply:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt
      - run: octodns-sync --config-file=config/octodns.yaml --doit
        env:
          GANDI_TOKEN: ${{ secrets.GANDI_TOKEN }}
        
```

## Google Workspace with Terraform

Because user management is not as standardized as DNS records, we'll have to use [Terraform](https://developer.hashicorp.com/terraform) here. 

Until Terraform can import automatically, you'll have to import your users and groups manually if you have an existing organization:

```hcl
import {
  to = googleworkspace_user.mb
  id = "mb@paug.fr"
}
```

Calling `terraform plan -generate-config-out=generated_resources.tf` pulls the full config for that user:

```hcl
resource "googleworkspace_user" "mb" {
  aliases                        = ["martin@paug.fr"]
  archived                       = false
  change_password_at_next_login  = false
  hash_function                  = null
  include_in_global_address_list = true
  ip_allowlist                   = false
  is_admin                       = true
  org_unit_path                  = "/"
  password                       = null # sensitive
  primary_email                  = "mb@paug.fr"
  recovery_email                 = "martin@mbonnin.net"
  recovery_phone                 = "+33688082143"
  suspended                      = false
  emails {
    address     = "mb@paug.fr"
    custom_type = null
    primary     = true
    type        = "other"
  }
  emails {
    address     = "martin@paug.fr"
    custom_type = null
    primary     = false
    type        = "other"
  }
  name {
    family_name = "Bonnin"
    given_name  = "Martin"
  }
}
```

Which you can then manage with Terraform:

```
$terraform plan
...
Apply complete! Resources: 0 added, 49 changed, 0 destroyed.
```

You can also manage groups with Terraform:

```hcl
resource "googleworkspace_group" "bureau" {
  aliases     = []
  description = null
  email       = "bureau@paug.fr"
  name        = "Bureau"
  timeouts {
    create = null
    update = null
  }
}

resource "googleworkspace_group_member" "bureau__mb" {
  delivery_settings = "ALL_MAIL"
  email             = "mb@paug.fr"
  group_id          = googleworkspace_group.bureau.id
  role              = "MEMBER"
  type              = "USER"
  timeouts {
    create = null
    update = null
  }
}
```

As for DNS, this is all automated through GitHub Actions. A pull request creates a plan, the merge triggers an update of the records:

```yaml
jobs:
  apply:
    name: Apply
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "~> 1.9"
      - run: terraform init
      - run: terraform apply -auto-approve -input=false
```

# Conclusion

This is just an example. You could manage everything in Terraform, or use [OpenTofu](https://opentofu.org/) or even Pulumi.

The important thing is to:
1. Give visibility to the team about the structure of your organization.
2. Empower the team to do the changes.

At this point, documentation, backup and rollbacks are the cherry on top. In all cases, there's really no reason to not use infrastructure as code for your organization in 2026.

_Comment on this post on [Bluesky](https://bsky.app/profile/mbonnin.net/post/3mtxuo6mps32u) or [Mastodon](https://mastodon.mbonnin.net/@mb/117160995090153108)_

---
[Photo](https://unsplash.com/photos/people-hiking-on-green-grass-field-during-daytime-Ms_p0I5DQSM) by [nika tchokhonelidze](https://unsplash.com/@nika9447)
