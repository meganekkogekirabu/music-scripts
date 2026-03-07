PREFIX ?=

NAME = tungbou

.PHONEY: install, uninstall, clean

install:
	install -Dm755 $(NAME).py $(PREFIX)/usr/bin/$(NAME)
	test -f "/etc/$(NAME).conf" || install -Dm644 $(NAME).sample.conf $(PREFIX)/etc/$(NAME).conf

uninstall:
	rm -f $(shell which $(NAME))
	rm -f /etc/$(NAME).conf

clean:
	rm -rf pkg src *.tar.zst
