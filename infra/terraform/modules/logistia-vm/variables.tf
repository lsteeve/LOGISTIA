variable "name"       { type = string }
variable "node_name"  { type = string }
variable "vmid"       { type = number }
variable "cores"      { type = number }
variable "memory"     { type = number }
variable "disk_size"  { type = number }
variable "datastore"  { type = string }
variable "ip"         { type = string }
variable "gateway"    { type = string }

variable "bridge" {
  type    = string
  default = "vmbr0"
}

variable "ssh_key" {
  type    = string
  default = ""
}

variable "userdata_id" {
  type    = string
  default = ""
}

variable "extra_nets" {
  type    = list(string)
  default = []
}
