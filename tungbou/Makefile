PREFIX ?= /usr/local

NAME = tungbou

.PHONEY: install, uninstall

install:
	install -Dm755 $(NAME).pl $(PREFIX)/bin/$(NAME)
	test -f "/etc/$(NAME).conf" || install -Dm644 $(NAME).sample.conf /etc/$(NAME).conf

uninstall:
	rm -f $(shell which $(NAME))
	rm -f /etc/$(NAME).conf
