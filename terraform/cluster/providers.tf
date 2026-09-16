terraform {
  required_providers {
    kind = {
      source  = "tehcyx/kind"
      version = "0.11.0"
    }
  }
}

provider "kind" {}