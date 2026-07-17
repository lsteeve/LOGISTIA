resource "proxmox_virtual_environment_vm" "logistia_vm" {
  name      = var.name
  node_name = var.node_name
  vm_id     = var.vmid
  on_boot   = true
  started   = true

  clone {
    vm_id     = 9000
    full      = true
    node_name = var.node_name
  }

  cpu {
    cores   = var.cores
    sockets = 1
    type    = var.cpu_type
  }

  memory {
    dedicated = var.memory
  }

  agent {
    enabled = true
    timeout = "30m"
  }

  disk {
    interface    = "scsi0"
    size         = var.disk_size
    datastore_id = var.datastore
    file_format  = "raw"
    discard      = "on"
  }

  network_device {
    bridge = var.bridge
    model  = "virtio"
  }

  dynamic "network_device" {
    for_each = var.extra_nets
    content {
      bridge = network_device.value
      model  = "virtio"
    }
  }

  initialization {
    ip_config {
      ipv4 {
        address = var.ip
        gateway = var.gateway
      }
    }

    user_account {
      username = "logistia"
      keys     = var.ssh_key != "" ? [var.ssh_key] : []
    }

    user_data_file_id = var.userdata_id
  }

  lifecycle {
    ignore_changes = [network_device, disk]
  }
}
